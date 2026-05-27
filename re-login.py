from main import Manager


def main():
    manager = Manager(host="http://192.168.210.175")
    manager.logout()
    manager.login()
    if manager.check().get("error") != "ok":
        manager.login()


if __name__ == "__main__":
    main()
