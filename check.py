import requests


def check_http(url="https://www.microsoft.com"):
    try:
        r = requests.get(url, timeout=3)
        return r.status_code == 200
    except Exception:
        return False


if not check_http():
    __import__("re-login").main()
