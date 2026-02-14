# Windows Packaging & Installation Guide

## Part 1: Building the Installer (Developer Machine)

### Prerequisites

- Python 3.10+
- PyInstaller (`pip install pyinstaller`)

### Step 1: Install Python dependencies

```
pip install -r launcher/requirements.txt pyinstaller
```

### Step 2: Build the launcher executable

```
python scripts/build.py
```

This produces a `dist/` directory containing:
- `LocalLLM.exe` — the launcher
- `docker-compose.yml`
- `.env`

### Step 3: Build the Windows installer with Inno Setup

[Inno Setup](https://jrsoftware.org/isinfo.php) is a free, open-source tool for creating Windows installer executables — the familiar "Next → Next → Install → Finish" wizards. It takes your files and wraps them into a single `Setup.exe` that handles installation to Program Files, Start Menu shortcuts, desktop icons, and a proper uninstaller. **Inno Setup only runs on Windows**, so you need a Windows machine or VM for this step.

1. Install [Inno Setup 6+](https://jrsoftware.org/isdl.php) on a Windows machine.
2. Copy the project to that machine (or access it via a shared folder).
3. Open `installer/setup.iss` in Inno Setup Compiler.
4. Click **Build → Compile** (or press Ctrl+F9).
5. The output `LocalLLM-Setup.exe` is created in `installer/Output/`.

> **Important:** Steps 2 and 3 must both be run on the Windows machine using Windows-native Python (not WSL). PyInstaller builds for the platform it runs on — running it in WSL produces a Linux binary that Windows cannot execute.

---

## Part 2: Sending to the User

Send the user the file:

```
LocalLLM-Setup.exe
```

Delivery options:
- **File sharing**: Google Drive, Dropbox, OneDrive, WeTransfer, etc.
- **USB drive**: Copy the file to a USB stick.
- **Self-hosted**: Host it on your own server or a GitHub Releases page.

> **Note:** Some email providers and browsers may flag `.exe` files. If the user has trouble downloading, try a different file sharing service or rename the extension temporarily.

---

## Part 3: Installation Steps (Windows User)

### System Requirements

- Windows 10 version 2004 (build 19041) or later, **or** Windows 11
- 8 GB RAM minimum (16 GB recommended)
- ~10 GB free disk space (for Docker images; more if downloading large models)
- Internet connection for the first launch
- Hardware virtualization enabled in BIOS/UEFI (Intel VT-x or AMD-V)

### Step 1: Install Docker Desktop

LocalLLM requires Docker Desktop, which must be installed first.

1. Go to https://www.docker.com/products/docker-desktop/
2. Click **Download for Windows**.
3. Run the `Docker Desktop Installer.exe`.
4. During installation, ensure **"Use WSL 2 instead of Hyper-V"** is checked.
5. Click **Ok** and wait for the installation to complete.
6. **Restart your computer** when prompted.
7. After reboot, Docker Desktop will launch automatically. Accept the license agreement.
8. Wait for Docker Desktop to show **"Docker Desktop is running"** in the system tray (bottom-right, near the clock).

> **Troubleshooting:** If Docker Desktop says "WSL 2 is not installed", open PowerShell as Administrator and run:
> ```
> wsl --install
> ```
> Then restart your computer and re-open Docker Desktop.

### Step 2: Install LocalLLM

1. Double-click `LocalLLM-Setup.exe`.
2. If Windows SmartScreen appears ("Windows protected your PC"), click **More info** → **Run anyway**.
3. Follow the installer prompts:
   - Choose an install location (default is fine).
   - Optionally create a desktop shortcut.
4. Click **Install**, then **Finish**.

### Step 3: First Launch

1. Open **LocalLLM** from the Start Menu or desktop shortcut.
2. A progress window will appear showing the setup status.
3. On the first launch, LocalLLM will automatically:
   - **Download the required Docker images** (~5–8 GB). This may take 10–30 minutes depending on your internet speed.
   - **Start the services** (Ollama AI engine + Web interface).
4. When everything is ready, your web browser will open to the chat interface.
5. Create an account (this is a local account stored only on your machine — no data leaves your computer).
6. Download a model from the admin panel and start chatting (see the README for instructions).

> **Important:** Do not close Docker Desktop while using LocalLLM. It should be running in the background (system tray icon).

### Step 4: Everyday Use

1. Make sure Docker Desktop is running (it starts automatically with Windows by default).
2. Open **LocalLLM** from the Start Menu or desktop shortcut.
3. The system tray icon will appear and the browser will open automatically.
4. When you're done, right-click the LocalLLM tray icon and select **Quit**.

No internet connection is needed after the first launch (unless downloading new models).

### Uninstalling

1. Open **Settings → Apps → Installed apps**.
2. Find **LocalLLM** and click **Uninstall**.
3. The uninstaller will stop the running containers and remove all files.

Optionally uninstall Docker Desktop separately if you no longer need it.

---

## Troubleshooting

| Problem | Solution |
|---|---|
| "Docker is not installed" message | Install Docker Desktop (see Step 1 above) |
| Docker Desktop won't start | Ensure hardware virtualization is enabled in your BIOS/UEFI settings |
| First launch is stuck on "Downloading" | Check your internet connection. The download is large (~5-8 GB) and may take time on slow connections |
| Browser opens but page doesn't load | Wait 1–2 minutes — the web interface takes time to initialize on first start |
| "Cannot connect" error in browser | Right-click the LocalLLM tray icon → **Start** to restart the services |
| Model responses are very slow | This is expected when running AI locally, especially on machines with less than 16 GB RAM. Responses may take a few seconds |
| Windows SmartScreen blocks the installer | Click **More info** → **Run anyway**. The installer is unsigned, which triggers this warning |
