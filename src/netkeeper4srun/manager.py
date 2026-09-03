from hashlib import sha1
from json import loads, dumps, load
from random import choice
from sys import stdout
from time import time, sleep
import re

from loguru import logger
from requests import Session

from .utils.base import b64encode
from .utils.device import devices
from .utils.hash import md5
from .utils.xencode import xencode

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36 Edg/148.0.0.0"
}
IP_REGEX = (
    r"((1\d{2}|25[0-5]|2[0-4]\d|[1-9]?\d)\.){3}(25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)"
)
LOG_FORMAT = (
    "<g>{time:MM/DD HH:mm:ss}</g> "
    "<c><u>NetKeeper4srun</u></c> "
    "[<lvl>{level}</lvl>] "
    "{message}"
)


class Manager(Session):

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(
        self,
        username: str = "",
        password: str = "",
        host: str = "",
        config_path: str = "srun_auth.json",
        log_path: str = "srun_login.log",
        logger_instance=logger,
    ):
        super().__init__()

        self.acid: int = 0
        self.n: str = "200"
        self.vtype: str = "1"
        self.enc_ver: str = "srun_bx1"
        self.token, self.checksum, self.info = None, None, None

        self.logger = logger_instance
        self.logger.remove()
        self.logger.add(log_path, rotation="1 MB", level="DEBUG", format=LOG_FORMAT)
        self.logger.add(stdout, level="INFO", format=LOG_FORMAT)

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                vars(self).update(load(f))
        except FileNotFoundError:
            pass

        if hasattr(self, "ac_id"):
            self.acid = int(self.ac_id)

        if username:
            self.username = username
        if password:
            self.password = password
        if host:
            self.host = host
        if [i for i in ["username", "password", "host"] if not hasattr(self, i)]:
            raise Exception

    def _jsonp(self, path: str, params: dict, prefix: str) -> dict:
        ts = round(time() * 1000)
        callback = f"{prefix}_{ts}"
        resp = self.get(
            self.host + path,
            headers=HEADERS,
            params={"callback": callback, "_": ts, **params},
        ).text
        return loads(resp.strip(callback + "()"))

    def _get_ip(self) -> str:
        for _ in range(3):
            resp = self.get(self.host + "/srun_portal_pc", headers=HEADERS).text
            m = re.search(IP_REGEX, resp)
            if m:
                return m.group()
            self.logger.warning("Failed to find IP in response, retrying...")
            sleep(1)
        self.logger.error("Failed to get IP after retries")
        raise RuntimeError("Failed to obtain IP")

    def login(self):
        ip = self._get_ip()
        resp = self._jsonp(
            "/cgi-bin/get_challenge",
            {"username": self.username, "ip": ip},
            "jQuery1124015280105355320628",
        )
        self.logger.debug(resp)
        self.token = resp["challenge"]
        self.logger.info(f"Token: {self.token}")
        self.info = "{SRBX1}" + b64encode(
            xencode(
                dumps(
                    {
                        "username": self.username,
                        "password": self.password,
                        "ip": ip,
                        "acid": str(self.acid),
                        "enc_ver": self.enc_ver,
                    }
                ),
                self.token,
            )
        )
        checksum = self.token + self.username
        checksum += self.token + md5(self.password, self.token)
        checksum += self.token + str(self.acid)
        checksum += self.token + ip
        checksum += self.token + self.n
        checksum += self.token + self.vtype
        checksum += self.token + self.info
        self.checksum = sha1(checksum.encode()).hexdigest()
        device = choice(devices)
        params = {
            "action": "login",
            "username": self.username,
            "password": "{MD5}" + md5(self.password, self.token),
            "os": device[0],
            "name": device[1],
            "double_stack": "0",
            "chksum": self.checksum,
            "info": self.info,
            "ac_id": str(self.acid),
            "ip": ip,
            "n": self.n,
            "type": self.vtype,
        }
        result: dict = self._jsonp(
            "/cgi-bin/srun_portal", params, "jQuery1124015280105355320628"
        )
        self.logger.debug(result)
        if result.get("suc_msg"):
            self.logger.success(
                f'login: {result["suc_msg"]} {self.username} {self.password} {result.get("online_ip")}'
            )
        else:
            msg = result.get("error_msg", "")
            self.logger.error(f'{result.get("error")}: {msg}')
            if any(k in msg for k in ("BAS", "Nas")):
                self.logger.error("ac_id error, retry in 5 seconds...")
                self.acid += 1
                sleep(5)
                self.login()
            elif "E2901" in msg:
                self.logger.error("username or password error...")
            elif "E2606" in msg:
                self.logger.error("user is disabled...")

    def logout(self):
        t = round(time())
        status = self.check()
        username = status.get("user_name") or self.username
        ip = status.get("online_ip") or self._get_ip()
        params = {
            "username": username,
            "ip": ip,
            "time": t,
            "unbind": "1",
            "sign": sha1(f"{t}{username}{ip}1{t}".encode()).hexdigest(),
        }
        result: dict = self._jsonp(
            "/cgi-bin/rad_user_dm", params, "jQuery112405185119642573086"
        )
        self.logger.debug(result)
        self.logger.info(f'logout: {result.get("error")}')

    def check(self) -> dict:
        result: dict = self._jsonp(
            "/cgi-bin/rad_user_info", {}, "jQuery112405185119642573086"
        )
        self.logger.debug(result)
        self.logger.info(f'check: {result.get("error")}')
        return result
