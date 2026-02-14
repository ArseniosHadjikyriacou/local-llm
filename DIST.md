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

### Step 3: Package for distribution

#### Option A: Zip the dist folder (simple, works from any OS)

Zip the entire `dist/` directory:

```
cd dist && zip -r ../LocalLLM.zip . && cd ..
```

This produces `LocalLLM.zip` that you send to the user. They extract it and run `LocalLLM.exe` directly — no installation step needed.

#### Option B: Build a Windows installer with Inno Setup (optional)

[Inno Setup](https://jrsoftware.org/isinfo.php) is a free, open-source tool for creating Windows installer executables — the familiar "Next → Next → Install → Finish" wizards. It takes your files and wraps them into a single `Setup.exe` that handles installation to Program Files, Start Menu shortcuts, desktop icons, and a proper uninstaller. **Inno Setup only runs on Windows**, so you need a Windows machine or VM for this step.

1. Install [Inno Setup 6+](https://jrsoftware.org/isdl.php) on a Windows machine.
2. Copy the project to that machine (or access it via a shared folder).
3. Open `installer/setup.iss` in Inno Setup Compiler.
4. Click **Build → Compile** (or press Ctrl+F9).
5. The output `LocalLLM-Setup.exe` is created in `installer/Output/`.

---

## Part 2: Sending to the User

Send the user one of:

- **`LocalLLM.zip`** (Option A) — user extracts and runs directly
- **`LocalLLM-Setup.exe`** (Option B) — user runs the installer

Delivery options:
- **File sharing**: Google Drive, Dropbox, OneDrive, WeTransfer, etc.
- **USB drive**: Copy the file to a USB stick.
- **Self-hosted**: Host it on your own server or a GitHub Releases page.

> **Note:** Some email providers and browsers may flag `.exe` or `.zip` files containing executables. If the user has trouble downloading, try a different file sharing service or rename the extension temporarily.

---

## Part 3: Installation Steps (Windows User)

### System Requirements

- Windows 10 version 2004 (build 19041) or later, **or** Windows 11
- 8 GB RAM minimum (16 GB recommended)
- ~15 GB free disk space (for Docker images + models)
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

**If you received `LocalLLM.zip`:**

1. Right-click the zip file and select **Extract All...**.
2. Choose a folder (e.g., your Desktop or Documents).
3. Click **Extract**.
4. Open the extracted folder — you should see `LocalLLM.exe`, `docker-compose.yml`, and `.env`.

**If you received `LocalLLM-Setup.exe`:**

1. Double-click `LocalLLM-Setup.exe`.
2. If Windows SmartScreen appears ("Windows protected your PC"), click **More info** → **Run anyway**.
3. Follow the installer prompts:
   - Choose an install location (default is fine).
   - Optionally create a desktop shortcut.
4. Click **Install**, then **Finish**.

### Step 3: First Launch

1. Open **LocalLLM** by double-clicking `LocalLLM.exe` (zip method) or from the Start Menu/desktop shortcut (installer method).
2. A small icon will appear in the system tray (bottom-right, near the clock).
3. On the first launch, LocalLLM will automatically:
   - **Download the required Docker images** (~5–8 GB). This may take 10–30 minutes depending on your internet speed.
   - **Start the services** (Ollama AI engine + Web interface).
   - **Download the AI model** (~2 GB). This may take another 5–15 minutes.
4. When everything is ready, your web browser will open to the chat interface.
5. Create an account (this is a local account stored only on your machine — no data leaves your computer).
6. Start chatting! Select **llama3.2:3b** from the model dropdown if it's not already selected.

> **Important:** Do not close Docker Desktop while using LocalLLM. It should be running in the background (system tray icon).

### Step 4: Everyday Use

1. Make sure Docker Desktop is running (it starts automatically with Windows by default).
2. Open **LocalLLM** by double-clicking `LocalLLM.exe` or from the Start Menu/desktop shortcut.
3. The system tray icon will appear and the browser will open automatically.
4. When you're done, right-click the LocalLLM tray icon and select **Quit**.

No internet connection is needed after the first launch.

### Uninstalling

**If you used the zip method:**

1. Right-click the LocalLLM tray icon → **Stop** (if running), then **Quit**.
2. Open a terminal (PowerShell or Command Prompt) and run:
   ```
   docker compose -f "C:\path\to\your\LocalLLM\docker-compose.yml" down -v
   ```
   (Replace the path with wherever you extracted the zip.)
3. Delete the extracted folder.

**If you used the installer:**

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
| First launch is stuck on "Pulling images" | Check your internet connection. The download is large (~7 GB) and may take time on slow connections |
| Browser opens but page doesn't load | Wait 1–2 minutes — the web interface takes time to initialize on first start |
| "Cannot connect" error in browser | Right-click the LocalLLM tray icon → **Start** to restart the services |
| Model responses are very slow | This is expected on machines with less than 16 GB RAM or without a dedicated GPU. The 3B model runs on CPU but is slower than cloud-based AI |
| Windows SmartScreen blocks the installer | Click **More info** → **Run anyway**. The installer is unsigned, which triggers this warning |
