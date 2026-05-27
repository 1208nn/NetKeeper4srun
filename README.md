# NetKeeper for srun

## Setup

- Python runtime `mise use -g uv@latest python@latest`
- Python packages `uv tool install git+https://github.com/1208nn/NetKeeper4srun.git`

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
35 6 * * * mise x -- uv tool run --from netkeeper4srun zjut-refresh
```

## Javascript Version

The JavaScript version of this project is already available now.
