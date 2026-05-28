# NetKeeper for srun / 莘岚霎迅

## Setup

- Python runtime `mise use -g uv python`
- Python package `mise use -g pipx:git+https://github.com/1208nn/NetKeeper4srun.git`

## Configure Sensitive Credentials

> [!WARNING]
> The following steps involve handling sensitive credentials. Ensure that you follow best practices for security and do not share your credentials with others.

```sh
touch srun_auth.json
edit srun_auth.json
```

## Usage

```sh
zjut-refresh
```

## Cron Job

```sh
crontab -e
```

Example configuration

```text
35 6 * * * mise x -- zjut-refresh
```

## Javascript Version

The JavaScript version of this project is already available now.

## Development

```sh
mise i
uv sync
```

## Use as a Python Library

### Installation

```sh
uv add git+https://github.com/1208nn/NetKeeper4srun.git
```

### Example Usage

```python
from netkeeper4srun import Manager

manager = Manager(
    username="your_username",  # optional, default is load from config file
    password="your_password",  # optional, default is load from config file
    host="your_host",  # optional, default is load from config file
    config_path="path_to_your_srun_auth.json",  # optional, default is "srun_auth.json"
)
manager.logout()  # Log out
manager.login()  # Log in
print(manager.check())  # Check status
```
