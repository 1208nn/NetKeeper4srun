from main import init


def main():
    manager = init()
    manager.logout()
    manager.login()
    if manager.check().get("error") != "ok":
        manager.login()


if __name__ == "__main__":
    main()
