from manager import Manager


def main():
    manager = Manager(host="http://192.168.210.175")
    manager.logout()
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
        main()


if __name__ == "__main__":
    main()
