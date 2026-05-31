# NetKeeper4srun JavaScript Version

JavaScript implementation of NetKeeper for srun Campus Network Login.

## Installation

### As a Command-Line Tool

```sh
npm install -g github:1208nn/NetKeeper4srun#JS
```

### As a Module

```sh
npm install github:1208nn/NetKeeper4srun#JS
```

## Configuration

Create a `srun_auth.json` file in your project directory:

```json
{
  "username": "your_username",
  "password": "your_password",
  "host": "http://192.168.210.175"
}
```

## Usage

### Command Line

```sh
srun
```

This will automatically:
1. Load credentials from `srun_auth.json`
2. Log out any existing session
3. Log in with your credentials
4. Log all output to `srun_login.log`

### As a Module

```javascript
import Manager from "netkeeper4srun-js";

async function main() {
  // Create manager (automatically loads config and initializes logger)
  const manager = new Manager(
    "",  // username (optional, loads from config if empty)
    "",  // password (optional, loads from config if empty)
    "http://192.168.210.175",  // host (optional, loads from config if empty)
    "srun_auth.json",  // configPath (optional, default: "srun_auth.json")
    "srun_login.log"   // logPath (optional, default: "srun_login.log")
  );

  // Logout existing session
  await manager.logout();

  // Login with credentials
  await manager.login();

  // Check status
  const status = await manager.check();
  console.log(status);
}

main().catch(console.error);
```

## Features

- **Automatic Configuration Loading**: Manager loads `srun_auth.json` automatically on initialization
- **Integrated Logging**: All logs are written to both console (with colors) and log file
- **Singleton Pattern**: Only one Manager instance can exist at a time
- **Error Handling**: Comprehensive error handling with detailed error messages
- **Retry Logic**: Automatic retry for transient failures
- **Device Spoofing**: Random device selection for login requests

## API

### Manager

#### Constructor

```javascript
new Manager(username, password, host, configPath, logPath)
```

- `username` (string, optional): Username for authentication
- `password` (string, optional): Password for authentication
- `host` (string, optional): Srun portal host URL
- `configPath` (string, optional): Path to config JSON file (default: "srun_auth.json")
- `logPath` (string, optional): Path to log file (default: "srun_login.log")

Any missing credential will attempt to be loaded from the config file.

#### Methods

##### `async login()`

Authenticate with the srun portal.

```javascript
await manager.login();
```

On success, logs a SUCCESS message. On failure, logs an ERROR message and may retry with different `ac_id` values.

##### `async logout()`

Logout from the srun portal.

```javascript
await manager.logout();
```

##### `async check()`

Check current authentication status.

```javascript
const status = await manager.check();
if (status.error === "ok") {
  console.log("Logged in as:", status.user_name);
}
```

Returns an object with the following properties:
- `error`: Status string ("ok" if authenticated)
- `user_name`: Current username (if authenticated)
- `online_ip`: Current IP address (if authenticated)
- Other properties depend on the srun implementation

## Logging

Logs are written to:
1. **Console**: Colored output with timestamps and log level
2. **File**: Plain text output to `srun_login.log` (or custom path)

Log levels: DEBUG, INFO, WARN, ERROR, SUCCESS

Log format:
```
MM/DD HH:mm:ss NetKeeper4srun [LEVEL] message
```

## Building

```sh
npm run build
```

This creates `srun.min.js` - a minified, bundled version suitable for deployment.

## Error Handling

Common errors and their causes:

- **"Failed to obtain IP"**: Cannot retrieve IP from srun portal
- **"ac_id error"**: Incorrect AC ID, will retry automatically with incremented value
- **"username or password error"**: Invalid credentials
- **"user is disabled"**: Account is disabled or 不在可用时段
- **"Missing required credentials"**: username, password, or host not provided or found in config
