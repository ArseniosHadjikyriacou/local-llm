# How LocalLLM Works

## Overview

LocalLLM is made up of three layers:

1. **Docker Compose stack** — two containers (Ollama and Open WebUI) that do the actual work.
2. **Python orchestration layer** — a system tray application that manages the lifecycle of the Docker stack so the user never has to touch a terminal.
3. **Windows installer** — packages the launcher and configuration files for distribution.

```
┌─────────────────────────────────────────────────────────────┐
│ User                                                        │
│   clicks tray icon                                          │
│       │                                                     │
│       ▼                                                     │
│ ┌───────────────────────────────────────────────────────┐   │
│ │ Python Orchestration Layer (launcher/)                 │   │
│ │                                                       │   │
│ │  main.py ──► tray_app.py ──┬── prerequisites.py       │   │
│ │                            └── docker_manager.py      │   │
│ │                                                       │   │
│ │  Talks to Docker via CLI                              │   │
│ └──────────┬────────────────────────────────────────────┘   │
│            │                                                │
│            ▼                                                │
│ ┌──────────────────┐   ┌──────────────────────────┐         │
│ │ Ollama Container │◄──│ Open WebUI Container     │         │
│ │ :11434           │   │ :3000                    │         │
│ │ Runs LLM models  │   │ Chat UI in the browser   │         │
│ └──────────────────┘   └──────────────────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

## Docker Compose Stack

Defined in `docker-compose.yml`. Two services:

- **ollama** (`ollama/ollama:latest`) — the LLM inference engine. Exposes a REST API on port 11434. Model weights are stored in a Docker volume (`ollama-data`) mounted at `/root/.ollama`, so they persist across restarts.
- **open-webui** (`ghcr.io/open-webui/open-webui:main`) — a web-based chat interface. Connects to Ollama internally via `http://ollama:11434`. Exposes port 3000 to the host. User data (accounts, chat history) is stored in a Docker volume (`webui-data`).

Open WebUI depends on Ollama (`depends_on`), so Docker always starts Ollama first. Both containers are set to `restart: unless-stopped`, meaning they come back automatically if they crash.

The `.env` file provides configurable values (ports, image tags) without modifying the compose file itself.

## Python Orchestration Layer

This is the core of what makes LocalLLM a turnkey product rather than a "run these docker commands" project. It lives in the `launcher/` directory and is compiled into a single Windows `.exe` via PyInstaller. The launcher handles everything the user would otherwise need a terminal for.

### Module Breakdown

#### `main.py` — Entry Point

Sets up logging (to both a file and stderr) and starts the tray application. When compiled with PyInstaller, this is what runs when the user double-clicks `LocalLLM.exe`.

- Log file location: `%LOCALAPPDATA%\LocalLLM\launcher.log`

#### `config.py` — Configuration

Central configuration module. Key responsibilities:

- **Path resolution**: Detects whether the app is running as a PyInstaller `.exe` (via `sys.frozen`) or as a normal Python script, and resolves paths accordingly. This is important because PyInstaller bundles files into a temporary directory at runtime.
- **Data directory**: Uses `%LOCALAPPDATA%\LocalLLM\` on Windows to store persistent data (marker files, logs) that survives app updates.
- **First-run marker**: A file (`.setup_complete`) in the data directory that tracks whether the one-time setup (Docker image pull) has been performed.

#### `prerequisites.py` — Dependency Checker

Runs before anything else on every launch. Checks that the system is ready:

1. **Is Docker installed?** Looks for the `docker` CLI on the system PATH using `shutil.which()`.
2. **Is the Docker daemon running?** Runs `docker info` and checks the exit code.
3. **Auto-start Docker Desktop**: If Docker is installed but not running, attempts to launch Docker Desktop from its known install paths (`C:\Program Files\Docker\...`) as a detached process, then polls `docker info` until the daemon responds (up to 120 seconds).
4. **Fallback**: If Docker is not installed at all, opens the Docker Desktop download page in the user's browser so they can install it.

#### `docker_manager.py` — Container Lifecycle

Manages the Docker Compose stack. All Docker commands run via `subprocess` with the compose file path explicitly specified (`docker compose -f <path> ...`).

Key functions:

- **`is_first_run()`** — Checks whether the `.setup_complete` marker file exists. If not, the first-run flow is triggered.
- **`pull_images(on_progress)`** — Runs `docker compose pull` to download the Ollama and Open WebUI Docker images. Streams stdout line-by-line and passes each line to an optional progress callback, which the tray app uses to update its tooltip.
- **`start()`** — Runs `docker compose up -d` to start both containers in detached mode.
- **`stop()`** — Runs `docker compose down` to stop and remove the containers (volumes are preserved).
- **`status()`** — Runs `docker compose ps` and parses the output to determine which containers are running.
- **`wait_for_ollama(timeout)`** — Polls `GET http://localhost:11434/api/tags` until Ollama responds. This is necessary because the container being "running" doesn't mean Ollama has finished loading.
- **`wait_for_webui(timeout)`** — Same polling approach for Open WebUI on port 3000.
- **`mark_setup_complete()`** — Writes the marker file so subsequent launches skip the first-run steps.

#### `progress_window.py` — Setup Progress Window

A tkinter-based window that appears during first-time setup to show the user what's happening. Uses a thread-safe queue so the startup flow (running in a background thread) can push log messages and status updates to the UI.

- **Bold status label** at the top (e.g., "Downloading Docker images...")
- **Scrollable log area** with a dark theme showing real-time progress
- Close button is disabled during setup (re-enabled on error so the user can dismiss it)
- Auto-closes when setup completes successfully

#### `tray_app.py` — System Tray UI

The user-facing interface. Uses `pystray` to create a Windows system tray icon with a right-click menu.

**Status management:**

The app tracks its state as one of: `stopped`, `starting`, `running`, `error`. Each state maps to an icon color (gray, yellow, green, red) generated dynamically with Pillow. The tooltip shows the current status and a detail message (e.g., "starting: Pulling Docker images...").

**Menu items:**

- **Start** — Triggers the startup flow in a background thread. Disabled when already running.
- **Stop** — Triggers shutdown. Disabled when not running.
- **Open WebUI** — Opens `http://localhost:3000` in the default browser. Disabled when not running.
- **Status** — Read-only display of the current state.
- **Quit** — Stops containers if running, then exits.

**Startup flow** (`_startup_flow`):

This is the main orchestration sequence, run in a background thread so the tray icon remains responsive:

```
Check prerequisites (prerequisites.py)
    │
    ▼ (fail → set error status, open Docker download page)
Is first run?
    │ yes → show progress window
    ▼
Pull Docker images (docker_manager.pull_images)
    │
    ▼
Start containers (docker_manager.start)
    │
    ▼
Wait for Ollama API to respond (docker_manager.wait_for_ollama)
    │
    ▼ (fail → set error status)
Wait for WebUI to respond (docker_manager.wait_for_webui)
    │
    ▼
Write first-run marker (docker_manager.mark_setup_complete)
    │
    ▼
Close progress window, set status to "running", open browser
```

On first run, a progress window shows real-time feedback for each step (image downloads, container startup, health checks). On subsequent launches, the image pull is skipped (the marker file exists), so startup is just: check prerequisites → start containers → wait for healthy → open browser.

Users download AI models themselves through the Open WebUI interface after setup is complete.

## Build & Packaging

### `scripts/build.py`

Automates the build process:

1. Cleans previous `build/` and `dist/` directories.
2. Runs PyInstaller with `--onefile --windowed` to produce a single `LocalLLM.exe` that runs without a console window.
3. Copies `docker-compose.yml` and `.env` into `dist/` alongside the executable.

### `installer/setup.iss`

An Inno Setup script that packages the contents of `dist/` into a Windows installer (`LocalLLM-Setup.exe`). Handles:

- Installing files to Program Files.
- Creating Start Menu and desktop shortcuts.
- Registering an uninstaller that runs `docker compose down` before removing files.
- Cleaning up the `%LOCALAPPDATA%\LocalLLM` data directory on uninstall.

## Data Locations

| What | Where |
|---|---|
| Launcher logs | `%LOCALAPPDATA%\LocalLLM\launcher.log` |
| First-run marker | `%LOCALAPPDATA%\LocalLLM\.setup_complete` |
| Ollama model weights | Docker volume `local-llm_ollama-data` |
| Open WebUI data (accounts, chats) | Docker volume `local-llm_webui-data` |
| Docker Compose config | Installed alongside `LocalLLM.exe` |
