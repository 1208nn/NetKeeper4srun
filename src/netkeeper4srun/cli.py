import sys
from time import sleep
import requests
from .manager import Manager

host = {
    "zjut": "192.168.210.175",
    "zjutpf": "192.168.210.171",
}


def refresh():
    manager = (
        Manager(host="http://" + host[sys.argv[1]])
        if len(sys.argv) > 1 and sys.argv[1] in host
        else Manager()
    )
    manager.logout()
    sleep(1)
    manager.login()
    sleep(1)
    if manager.check().get("error") != "ok":
        manager.login()


def check():

    def check_http(url="https://www.microsoft.com"):
        try:
            r = requests.get(url, timeout=3)
            return r.status_code == 200
        except Exception:
            return False

    if not check_http():
        refresh()


if __name__ == "__main__":
    refresh()
