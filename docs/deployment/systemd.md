# systemd Service (Linux)

Friday includes a systemd unit file for running the API server as a managed background service on Linux. This provides automatic startup on boot, crash recovery, and integration with standard Linux service management tools.

## Prerequisites

Before installing the service, ensure that:

1. Friday is installed in a virtual environment at `/opt/friday/.venv` (or adjust paths accordingly).
2. A dedicated `friday` system user exists (recommended for security).
3. An inference engine (such as Ollama) is running and accessible.

Create the user and installation directory:

```bash
sudo useradd --system --create-home --home-dir /opt/friday friday
sudo -u friday python3 -m venv /opt/friday/.venv
sudo -u friday git clone https://github.com/purnasai1807-lgtm/Friday_AI.git /opt/friday/Friday
cd /opt/friday/Friday && sudo -u friday uv sync --extra server
```

## Installing the Service

Copy the unit file to the systemd directory, reload the daemon, and enable the service:

```bash
sudo cp deploy/systemd/friday.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable friday
sudo systemctl start friday
```

Verify it is running:

```bash
sudo systemctl status friday
```

## Service File Reference

The provided unit file at `deploy/systemd/friday.service`:

```ini
[Unit]
Description=Friday API Server
After=network.target

[Service]
Type=simple
User=friday
WorkingDirectory=/opt/friday
ExecStart=/opt/friday/.venv/bin/friday serve --host 0.0.0.0 --port 8000
Restart=on-failure
RestartSec=5
Environment=HOME=/opt/friday

[Install]
WantedBy=multi-user.target
```

### `[Unit]` Section

| Directive     | Value              | Description                                                                 |
|---------------|--------------------|-----------------------------------------------------------------------------|
| `Description` | `Friday API Server` | Human-readable name shown in `systemctl status` and logs.              |
| `After`       | `network.target`   | Delays startup until the network stack is available, since the server binds to a network socket and may need to reach a remote engine. |

### `[Service]` Section

| Directive          | Value                                                              | Description                                                                                     |
|--------------------|--------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| `Type`             | `simple`                                                           | The process started by `ExecStart` is the main service process. systemd considers the service started immediately. |
| `User`             | `friday`                                                       | Runs the server as the `friday` user rather than root, limiting the blast radius of any security issue. |
| `WorkingDirectory` | `/opt/friday`                                                  | Sets the working directory for the process. This is where Friday looks for local files and writes data. |
| `ExecStart`        | `/opt/friday/.venv/bin/friday serve --host 0.0.0.0 --port 8000` | The command to start the server. Uses the full path to the `friday` binary inside the virtual environment. |
| `Restart`          | `on-failure`                                                       | Automatically restarts the service if it exits with a non-zero exit code. Does not restart on clean shutdown (`systemctl stop`). |
| `RestartSec`       | `5`                                                                | Waits 5 seconds before attempting a restart, preventing rapid restart loops if the service crashes immediately on startup. |
| `Environment`      | `HOME=/opt/friday`                                             | Sets the `HOME` environment variable so Friday finds its configuration at `~/.friday/config.toml` (resolving to `/opt/friday/.friday/config.toml`). |

### `[Install]` Section

| Directive    | Value               | Description                                                                                 |
|--------------|---------------------|---------------------------------------------------------------------------------------------|
| `WantedBy`   | `multi-user.target` | The service starts when the system reaches multi-user mode (standard boot target for servers). `systemctl enable` creates a symlink under this target. |

## Configuration Options

### Changing the Bind Address and Port

Edit the `ExecStart` line to change the host or port:

```ini
ExecStart=/opt/friday/.venv/bin/friday serve --host 127.0.0.1 --port 9000
```

!!! tip
    Binding to `127.0.0.1` restricts access to localhost only. Use this when running behind a reverse proxy like Nginx or Caddy.

### Setting the Engine and Model

Pass additional flags to `friday serve`:

```ini
ExecStart=/opt/friday/.venv/bin/friday serve --host 0.0.0.0 --port 8000 --engine ollama --model qwen3:8b
```

### Adding Environment Variables

Add multiple `Environment` directives or use `EnvironmentFile` for complex configurations:

```ini
[Service]
Environment=HOME=/opt/friday
Environment=OPENJARVIS_ENGINE_DEFAULT=vllm
Environment=OPENJARVIS_OLLAMA_HOST=http://localhost:11434
```

Or load from a file:

```ini
[Service]
EnvironmentFile=/opt/friday/.env
```

### Changing the User

If you prefer a different service user, update both the `User` directive and the paths:

```ini
[Service]
User=myuser
WorkingDirectory=/home/myuser/friday
ExecStart=/home/myuser/friday/.venv/bin/friday serve --host 0.0.0.0 --port 8000
Environment=HOME=/home/myuser/friday
```

### Using a Configuration File

Ensure the configuration file exists at the path where `HOME` points:

```bash
sudo -u friday mkdir -p /opt/friday/.friday
sudo -u friday cp config.toml /opt/friday/.friday/config.toml
```

The server reads `~/.friday/config.toml` on startup, where `~` resolves from the `HOME` environment variable.

## Viewing Logs

Friday logs are captured by journald. View them with `journalctl`:

```bash
# View all logs for the service
sudo journalctl -u friday

# Follow logs in real time
sudo journalctl -u friday -f

# View logs since the last boot
sudo journalctl -u friday -b

# View logs from the last hour
sudo journalctl -u friday --since "1 hour ago"

# View only error-level messages
sudo journalctl -u friday -p err
```

## Managing the Service

### Start, Stop, and Restart

```bash
# Start the service
sudo systemctl start friday

# Stop the service
sudo systemctl stop friday

# Restart the service (stop + start)
sudo systemctl restart friday

# Reload configuration without full restart (sends SIGHUP)
sudo systemctl reload-or-restart friday
```

### Check Status

```bash
sudo systemctl status friday
```

Example output:

```
● friday.service - Friday API Server
     Loaded: loaded (/etc/systemd/system/friday.service; enabled; preset: enabled)
     Active: active (running) since Fri 2026-02-21 10:00:00 UTC; 2h ago
   Main PID: 12345 (friday)
      Tasks: 4 (limit: 4915)
     Memory: 256.0M
        CPU: 1min 23s
     CGroup: /system.slice/friday.service
             └─12345 /opt/friday/.venv/bin/python /opt/friday/.venv/bin/friday serve --host 0.0.0.0 --port 8000
```

### Enable and Disable on Boot

```bash
# Enable automatic start on boot
sudo systemctl enable friday

# Disable automatic start on boot
sudo systemctl disable friday
```

### Apply Changes After Editing the Unit File

After modifying `/etc/systemd/system/friday.service`, reload the systemd daemon and restart the service:

```bash
sudo systemctl daemon-reload
sudo systemctl restart friday
```

## Running Alongside Ollama

If Ollama is also managed via systemd, you can add an ordering dependency so the Friday service waits for Ollama to start:

```ini
[Unit]
Description=Friday API Server
After=network.target ollama.service
Requires=ollama.service
```

| Directive  | Description                                                              |
|------------|--------------------------------------------------------------------------|
| `After`    | Ensures Friday starts after Ollama.                                  |
| `Requires` | If Ollama fails to start, Friday will not start either.              |

!!! note
    Use `Wants` instead of `Requires` if you want Friday to start even when Ollama is unavailable (for example, if you plan to start Ollama manually later).
