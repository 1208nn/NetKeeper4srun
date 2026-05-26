# NetKeeper for srun

## Setup

- Python runtime `mise i`
- Python packages `uv sync`

## Configure Sensitive Credentials

> [!WARNING]
> The following steps involve handling sensitive credentials. Ensure that you follow best practices for security and do not share your credentials with others.

```sh
cp srun_auth.json.template srun_auth.json
edit srun_auth.json
ln srun_auth.json ~/.srun_auth.json
```

## Usage

```sh
uv run re-login.py
uv run check.py # Only relogin if no Internet connection
```

## Cron Job Example

```text
0 6 * * * mise x uv -- uv run /home/shy/NetKeeper4srun/re-login.py
```

## Javascript Version

The JavaScript version of this project is already available now.
