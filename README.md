# LocalLLM

A private, offline AI chat application that runs entirely on your computer. No data ever leaves your machine.

## What You Need

- **Windows 10** (version 2004 or later) or **Windows 11**
- **8 GB RAM** minimum (16 GB recommended)
- **10 GB free disk space**
- **Internet connection** for the initial setup only

## Installation

### 1. Install Docker Desktop

LocalLLM uses Docker to run behind the scenes. You only need to install it once.

1. Go to https://www.docker.com/products/docker-desktop/
2. Click **Download for Windows**.
3. Run `Docker Desktop Installer.exe`.
4. During installation, make sure **"Use WSL 2 instead of Hyper-V"** is checked.
5. Click **Ok** and wait for installation to finish.
6. **Restart your computer** when prompted.
7. After reboot, Docker Desktop will open automatically. Accept the license agreement.
8. Wait until you see **"Docker Desktop is running"** in the system tray (bottom-right corner, near the clock).

> If Docker Desktop says "WSL 2 is not installed", open PowerShell as Administrator and run `wsl --install`, then restart your computer.

### 2. Install LocalLLM

1. Double-click `LocalLLM-Setup.exe`.
2. If Windows shows a **"Windows protected your PC"** warning, click **More info** then **Run anyway**. This is normal for unsigned software.
3. Follow the prompts — the defaults are fine.
4. Click **Install**, then **Finish**.

### 3. First Launch

1. Open **LocalLLM** from the Start Menu or desktop shortcut.
2. A small icon will appear in the system tray (bottom-right corner).
3. LocalLLM will automatically set itself up. This only happens once and requires an internet connection:
   - **Downloading components** (~5-8 GB) — 10 to 30 minutes depending on your internet speed.
4. When everything is ready, your browser will open to the chat interface.
5. Create an account. This is a **local account** stored only on your computer — it is not sent anywhere.
6. Download a model (see **Downloading Models** below) and start chatting!

> Do not close Docker Desktop while using LocalLLM. It needs to be running in the background.

## Everyday Use

1. Make sure Docker Desktop is running (it starts automatically with Windows by default).
2. Open **LocalLLM** from the Start Menu or desktop shortcut.
3. Your browser will open automatically to the chat interface.
4. When you're done, right-click the LocalLLM icon in the system tray and select **Quit**.

After the first launch, **no internet connection is needed** (unless you want to download more models). Everything runs locally on your machine.

## Downloading Models

LocalLLM does not come with any AI models pre-installed. You need to download at least one model before you can start chatting. This requires an internet connection.

1. Open the chat interface in your browser (http://localhost:3000).
2. Click on your **profile icon** in the top-right corner.
3. Go to **Admin Panel** → **Settings** → **Connection**.
4. Under **Ollama API** , click the download icon.
5. Select the model you want and click the download button.
6. Wait for the download to complete. Larger models can take a while.
7. Once downloaded, the new model will appear in the model dropdown on the chat screen.

### Recommended Models

| Model | Size | Description |
|---|---|---|
| `llama3.2:3b` | ~2 GB | Good balance of speed and quality. Recommended starting point |
| `llama3.2:1b` | ~1.3 GB | Smaller and faster, but less capable |
| `llama3.1:8b` | ~4.7 GB | Better quality responses, but needs more RAM and is slower |
| `phi4-mini` | ~2.5 GB | Microsoft's compact model, strong reasoning for its size |

You can browse all available models at https://ollama.com/library

> **Note:** Larger models require more RAM and disk space. If your computer has 8 GB of RAM, stick with models 3B or smaller. With 16 GB or more, you can try the 8B models.

## Uninstalling

1. Open **Settings → Apps → Installed apps**.
2. Find **LocalLLM** and click **Uninstall**.
3. If you no longer need Docker Desktop, you can uninstall it separately from the same page.

## Troubleshooting

| Problem | What to do |
|---|---|
| "Docker is not installed" message | Install Docker Desktop (see step 1 above) |
| Docker Desktop won't start | Make sure hardware virtualization is enabled in your BIOS/UEFI. Search online for instructions specific to your computer model |
| Setup seems stuck on "Downloading" | Check your internet connection. The initial download is large and can take a while on slower connections |
| Browser opens but the page won't load | Wait a couple of minutes. The interface can take some time to start, especially on the first launch |
| "Cannot connect" error in browser | Right-click the LocalLLM tray icon and click **Start** to restart the services |
| AI responses are slow | This is normal when running AI locally, especially on machines with less than 16 GB of RAM. Responses may take a few seconds |
| Windows SmartScreen blocks the installer | Click **More info** then **Run anyway** |

## Privacy

LocalLLM runs completely on your computer. Your conversations, data, and files are never uploaded to the internet. Once the initial setup is complete, LocalLLM works fully offline.
