import threading
import webbrowser
import logging
import os
import sys

import pystray
from PIL import Image, ImageDraw

from launcher.config import APP_NAME, WEBUI_URL
from launcher import prerequisites, docker_manager
from launcher.progress_window import ProgressWindow

logger = logging.getLogger(__name__)


class TrayApp:
    """System tray application that manages the LocalLLM stack."""

    def __init__(self):
        self._status = "stopped"  # stopped | starting | running | error
        self._status_detail = ""
        self._lock = threading.Lock()
        self._icon = None
        self._progress = None  # ProgressWindow instance during setup

    # ── Icon generation ──────────────────────────────────────────────

    def _create_icon_image(self, color="gray"):
        """Generate a simple colored circle icon."""
        colors = {
            "gray": "#808080",
            "green": "#00CC00",
            "yellow": "#FFAA00",
            "red": "#CC0000",
        }
        fill = colors.get(color, colors["gray"])
        img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.ellipse([4, 4, 60, 60], fill=fill)
        return img

    def _icon_for_status(self):
        status_colors = {
            "stopped": "gray",
            "starting": "yellow",
            "running": "green",
            "error": "red",
        }
        return self._create_icon_image(status_colors.get(self._status, "gray"))

    # ── Status management ────────────────────────────────────────────

    def _set_status(self, status, detail=""):
        with self._lock:
            self._status = status
            self._status_detail = detail
        self._update_icon()

    def _update_icon(self):
        """Update the tray icon image and tooltip to reflect current status.

        Skipped while the progress window is visible (first-run setup) to
        avoid cross-thread Shell_NotifyIcon calls on Windows that can
        cause the icon to silently fail to appear.
        """
        if self._icon and not self._progress:
            try:
                self._icon.icon = self._icon_for_status()
                self._icon.title = self._tooltip()
            except Exception as e:
                logger.warning("Failed to update tray icon: %s", e)

    def _tooltip(self):
        tip = f"{APP_NAME} — {self._status}"
        if self._status_detail:
            tip += f": {self._status_detail}"
        return tip

    # ── Progress window helpers ──────────────────────────────────────

    def _progress_log(self, message):
        """Log a message to both the logger and the progress window."""
        logger.info(message)
        if self._progress:
            self._progress.log(message)

    def _progress_status(self, message):
        """Update the status label in the progress window."""
        if self._progress:
            self._progress.set_status(message)

    # ── Menu actions ─────────────────────────────────────────────────

    def _on_start(self, icon, item):
        if self._status == "running":
            return
        thread = threading.Thread(target=self._startup_flow, daemon=True)
        thread.start()

    def _on_stop(self, icon, item):
        if self._status not in ("running", "error"):
            return
        thread = threading.Thread(target=self._shutdown_flow, daemon=True)
        thread.start()

    def _on_open_webui(self, icon, item):
        webbrowser.open(WEBUI_URL)

    def _on_quit(self, icon, item):
        if self._status == "running":
            try:
                docker_manager.stop()
            except Exception as e:
                logger.error("Error stopping on quit: %s", e)
        icon.stop()

    # ── Menu builder ─────────────────────────────────────────────────

    def _build_menu(self):
        return pystray.Menu(
            pystray.MenuItem("Start", self._on_start, enabled=lambda _: self._status != "running"),
            pystray.MenuItem("Stop", self._on_stop, enabled=lambda _: self._status in ("running", "error")),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Open WebUI", self._on_open_webui, enabled=lambda _: self._status == "running"),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                lambda _: f"Status: {self._status}" + (f" ({self._status_detail})" if self._status_detail else ""),
                None,
                enabled=False,
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", self._on_quit),
        )

    # ── Startup / shutdown flows ─────────────────────────────────────

    def _startup_flow(self):
        """Full startup sequence: prerequisites → pull → start → open."""
        first_run = docker_manager.is_first_run()

        # Show progress window during first-run setup
        if first_run:
            self._progress = ProgressWindow()
            self._progress.show()
            self._progress.set_status("Checking prerequisites...")
            self._progress.log("First-time setup — this may take 10-30 minutes.")
            self._progress.log("Please keep this window open and stay connected to the internet.\n")

        try:
            self._set_status("starting", "Checking prerequisites...")
            self._progress_log("Checking for Docker Desktop...")
            ok, msg = prerequisites.check_prerequisites()
            if not ok:
                self._set_status("error", "Docker not available")
                logger.error("Prerequisites check failed: %s", msg)
                if self._progress:
                    self._progress.set_error("Docker Desktop is not available")
                    self._progress.log(f"\n{msg}")
                if "not installed" in msg.lower():
                    prerequisites.open_docker_download_page()
                return
            self._progress_log("Docker Desktop is ready.")

            # First-run: pull images
            if first_run:
                self._set_status("starting", "Pulling Docker images (first run)...")
                self._progress_status("Downloading Docker images...")
                self._progress_log("\nPulling Docker images (this is the largest download)...")

                def on_image_progress(line):
                    self._set_status("starting", line[:60])
                    self._progress_log(line)

                docker_manager.pull_images(on_progress=on_image_progress)
                self._progress_log("Docker images downloaded successfully.\n")

            self._set_status("starting", "Starting containers...")
            self._progress_log("Starting containers...")
            self._progress_status("Starting containers...")
            docker_manager.start()
            self._progress_log("Containers started.")

            self._set_status("starting", "Waiting for Ollama...")
            self._progress_log("Waiting for Ollama to be ready...")
            self._progress_status("Waiting for Ollama...")
            if not docker_manager.wait_for_ollama(timeout=180):
                self._set_status("error", "Ollama not responding")
                if self._progress:
                    self._progress.set_error("Error: Ollama did not respond in time")
                    self._progress.log("\nOllama failed to start. Check Docker Desktop is running and try again.")
                return
            self._progress_log("Ollama is ready.")

            self._set_status("starting", "Waiting for WebUI...")
            self._progress_log("Waiting for web interface to be ready...")
            self._progress_status("Starting web interface...")
            if not docker_manager.wait_for_webui(timeout=180):
                self._set_status("error", "WebUI not responding")
                if self._progress:
                    self._progress.set_error("Error: Web interface did not respond in time")
                    self._progress.log("\nThe web interface failed to start. Try restarting the application.")
                return
            self._progress_log("Web interface is ready.")

            if first_run:
                docker_manager.mark_setup_complete()

            self._set_status("running")

            if self._progress:
                self._progress_log("\nSetup complete! Opening your browser...")
                self._progress.set_status("Setup complete!")
                import time
                time.sleep(2)
                self._progress.close()
                self._progress = None
                # Now that the progress window is gone, sync the tray icon
                self._update_icon()

            webbrowser.open(WEBUI_URL)

        except Exception as e:
            logger.exception("Startup failed")
            self._set_status("error", str(e)[:80])
            if self._progress:
                self._progress.set_error("Setup failed")
                self._progress.log(f"\nError: {e}")

    def _shutdown_flow(self):
        """Stop the compose stack."""
        try:
            self._set_status("starting", "Stopping...")
            docker_manager.stop()
            self._set_status("stopped")
        except Exception as e:
            logger.exception("Shutdown failed")
            self._set_status("error", str(e)[:80])

    # ── Run ──────────────────────────────────────────────────────────

    def run(self, auto_start=True):
        """Create and run the system tray icon. Blocks until quit."""
        icon_image = self._icon_for_status()
        self._icon = pystray.Icon(
            APP_NAME,
            icon=icon_image,
            title=self._tooltip(),
            menu=self._build_menu(),
        )

        def on_ready(icon):
            # Return immediately so pystray fully registers the icon.
            # Run the startup in its own thread to avoid blocking the
            # setup callback, which can prevent the tray icon from
            # appearing on Windows.
            if auto_start:
                thread = threading.Thread(target=self._startup_flow, daemon=True)
                thread.start()

        # icon.run() blocks the main thread (runs the OS message loop).
        # The setup callback runs in a separate thread once the icon is visible.
        self._icon.run(setup=on_ready)
