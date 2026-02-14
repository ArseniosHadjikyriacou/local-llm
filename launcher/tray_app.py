import threading
import webbrowser
import logging
import os
import sys

import pystray
from PIL import Image, ImageDraw

from launcher.config import APP_NAME, WEBUI_URL
from launcher import prerequisites, docker_manager, model_manager

logger = logging.getLogger(__name__)


class TrayApp:
    """System tray application that manages the LocalLLM stack."""

    def __init__(self):
        self._status = "stopped"  # stopped | starting | running | error
        self._status_detail = ""
        self._lock = threading.Lock()
        self._icon = None

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
        if self._icon:
            self._icon.icon = self._icon_for_status()
            self._icon.title = self._tooltip()

    def _tooltip(self):
        tip = f"{APP_NAME} — {self._status}"
        if self._status_detail:
            tip += f": {self._status_detail}"
        return tip

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
        """Full startup sequence: prerequisites → pull → start → models → open."""
        try:
            self._set_status("starting", "Checking prerequisites...")
            ok, msg = prerequisites.check_prerequisites()
            if not ok:
                self._set_status("error", "Docker not available")
                logger.error("Prerequisites check failed: %s", msg)
                # Open download page if Docker is missing
                if "not installed" in msg.lower():
                    prerequisites.open_docker_download_page()
                return

            # First-run: pull images and models
            if docker_manager.is_first_run():
                self._set_status("starting", "Pulling Docker images (first run)...")
                docker_manager.pull_images(
                    on_progress=lambda line: self._set_status("starting", line[:60])
                )

            self._set_status("starting", "Starting containers...")
            docker_manager.start()

            self._set_status("starting", "Waiting for Ollama...")
            if not docker_manager.wait_for_ollama(timeout=180):
                self._set_status("error", "Ollama not responding")
                return

            # Pull models on first run
            if docker_manager.is_first_run():
                self._set_status("starting", "Downloading models (first run)...")
                model_manager.pull_default_models(
                    on_progress=lambda name, status, done, total: self._set_status(
                        "starting",
                        f"{name}: {status}" + (f" {done * 100 // total}%" if total else ""),
                    )
                )
                docker_manager.mark_setup_complete()

            self._set_status("starting", "Waiting for WebUI...")
            if not docker_manager.wait_for_webui(timeout=180):
                self._set_status("error", "WebUI not responding")
                return

            self._set_status("running")
            webbrowser.open(WEBUI_URL)

        except Exception as e:
            logger.exception("Startup failed")
            self._set_status("error", str(e)[:80])

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
            if auto_start:
                self._startup_flow()

        # icon.run() blocks the main thread (runs the OS message loop).
        # The setup callback runs in a separate thread once the icon is visible.
        self._icon.run(setup=on_ready)
