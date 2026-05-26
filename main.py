#!/usr/bin/env python3

from hashlib import sha1
from json import loads, dumps, load
from random import choice
from sys import stdout
from time import time, sleep
import re

from loguru import logger
from requests import Session

from utils.base import b64encode
from utils.device import devices
from utils.hash import md5
from utils.xencode import xencode

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36 Edg/148.0.0.0"
}
IP_REGEX = (
    r"((1\d{2}|25[0-5]|2[0-4]\d|[1-9]?\d)\.){3}(25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)"
)


class Manager(Session):

    def __init__(self, username: str = "", password: str = ""):
        super().__init__()
        self.acid: int = 0
        self.n: str = "200"
        self.vtype: str = "1"
        self.enc_ver: str = "srun_bx1"
        self.username = username
        self.password = password
        self.logger = logger
        self.host = self.get_host()
        self.token, self.checksum, self.info = None, None, None

    def _jsonp(self, path: str, params: dict, prefix: str) -> dict:
        ts = round(time() * 1000)
        callback = f"{prefix}_{ts}"
        resp = self.get(
            self.host + path,
            headers=HEADERS,
            params={"callback": callback, "_": ts, **params},
        ).text
        return loads(resp.strip(callback + "()"))

    def get_host(self):
        host = "http://192.168.210.175"
        try:
            self.get(host)
            return host
        except Exception as e:
            self.logger.info(f"Host {host} {e}")
        self.logger.error("Failed to get host...")
        exit(-1)

    def get_ip(self) -> str:
        for _ in range(3):
            resp = self.get(self.host + "/srun_portal_pc", headers=HEADERS).text
            m = re.search(IP_REGEX, resp)
            if m:
                return m.group()
            self.logger.warning("Failed to find IP in response, retrying...")
            sleep(1)
        self.logger.error("Failed to get IP after retries")
        raise RuntimeError("Failed to obtain IP")

    def get_token(self) -> str:
        resp = self._jsonp(
            "/cgi-bin/get_challenge",
            {"username": self.username, "ip": self.get_ip()},
            "jQuery1124015280105355320628",
        )
        self.logger.debug(resp)
        token = resp["challenge"]
        self.logger.info(f"Token: {token}")
        return token

    def get_info(self) -> str:
        return "{SRBX1}" + b64encode(
            xencode(
                dumps(
                    {
                        "username": self.username,
                        "password": self.password,
                        "ip": self.get_ip(),
                        "acid": str(self.acid),
                        "enc_ver": self.enc_ver,
                    }
                ),
                self.token,
            )
        )

    def get_checksum(self) -> str:
        checksum = self.token + self.username
        checksum += self.token + md5(self.password, self.token)
        checksum += self.token + str(self.acid)
        checksum += self.token + self.get_ip()
        checksum += self.token + self.n
        checksum += self.token + self.vtype
        checksum += self.token + self.info
        return sha1(checksum.encode()).hexdigest()

    def login(self) -> dict:
        self.token = self.get_token()
        self.info = self.get_info()
        self.checksum = self.get_checksum()
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
            "ip": self.get_ip(),
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
                result = self.login()
            elif "E2901" in msg or "E2606" in msg:
                self.logger.error(
                    "username or password error..."
                    if "E2901" in msg
                    else "user is disabled..."
                )
                result["error_msg"] = "4xx"
        return result

    def logout(self) -> dict:
        t = round(time())
        status = self.check()
        username = status.get("user_name") or self.username
        ip = status.get("online_ip") or self.get_ip()
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
        return result

    def check(self) -> dict:
        result: dict = self._jsonp(
            "/cgi-bin/rad_user_info", {}, "jQuery112405185119642573086"
        )
        self.logger.debug(result)
        self.logger.info(f'check: {result.get("error")}')
        return result

    def pick_auth(self, auths) -> None:
        auth = choice(auths)
        self.username, self.password = auth["username"], auth["password"]

    def login_with_retry(self, auths) -> None:
        while self.login().get("error_msg") == "4xx":
            self.pick_auth(auths)
            logger.debug("username or password is incorrect, retry in 2 seconds...")
            sleep(2)

    def refresh(self, auths) -> None:
        logger.debug("Try to refresh...")
        self.pick_auth(auths)
        self.logout()
        self.login_with_retry(auths)

    def ensure_login(self, auths) -> None:
        logger.debug("Check status...")
        status = self.check()
        if status.get("error") != "ok":
            logger.warning(f"{status.get('error')}, try to login...")
            self.pick_auth(auths)
            self.login_with_retry(auths)


def main():
    logger.remove()
    logger.add(
        "srun_login.log",
        rotation="1 MB",
        level="DEBUG",
        format="<g>{time:MM-DD HH:mm:ss}</g> [<lvl>{level}</lvl>] <c><u>srun_login</u></c> | {message}",
    )
    logger.add(
        stdout,
        level="INFO",
        format="<g>{time:MM-DD HH:mm:ss}</g> [<lvl>{level}</lvl>] <c><u>srun_login</u></c> | {message}",
    )
    try:
        with open("srun_auth.json", "r", encoding="utf-8") as f:
            auths = load(f)
    except Exception as e:
        logger.bind(module="srun_login").error(f"{e}, please check srun_auth.json")
        exit(-1)
    logger.info("Process started")
    manager = Manager()
    manager.refresh(auths)
    manager.ensure_login(auths)


if __name__ == "__main__":
    main()
