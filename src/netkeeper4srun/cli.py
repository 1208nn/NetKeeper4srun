from sys import argv
from time import sleep
from .manager import Manager

host = {
    "zjut": "192.168.210.175",
}


def refresh():
    manager = Manager(host="http://" + host[argv[1]])
    manager.logout()
    sleep(1)
    manager.login()
    if manager.check().get("error") != "ok":
        manager.login()


def check():
    import requests

    def check_http(url="https://www.microsoft.com"):
        try:
            r = requests.get(url, timeout=3)
            return r.status_code == 200
        except Exception:
            return False

    if not check_http():
        refresh()
