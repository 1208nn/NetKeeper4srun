# NetKeeper for srun

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
