"""Main application window — replaces the system tray icon with a visible
tkinter window that shows status, logs, and control buttons.

The window runs tkinter's mainloop on the main thread. Long-running
operations (startup, shutdown) run in background threads and push
updates via a thread-safe queue.
"""

import queue
import threading
import time
import tkinter as tk
from tkinter import scrolledtext
import webbrowser
import logging

from launcher.config import APP_NAME, APP_VERSION, WEBUI_URL
from launcher import prerequisites, docker_manager

logger = logging.getLogger(__name__)

STATUS_COLORS = {
    "stopped": "#808080",
    "starting": "#FFAA00",
    "running": "#00CC00",
    "error": "#CC0000",
}


class AppWindow:
    """Main control window for LocalLLM."""

    def __init__(self):
        self._status = "stopped"
        self._queue = queue.Queue()
        self._root = None

    # ── Build the UI ─────────────────────────────────────────────────

    def _build(self):
        self._root = tk.Tk()
        self._root.title(f"{APP_NAME}")
        self._root.geometry("620x420")
        self._root.resizable(True, True)
        self._root.protocol("WM_DELETE_WINDOW", self._on_quit)

        # ── Top bar: status indicator + buttons ──
        top = tk.Frame(self._root)
        top.pack(fill="x", padx=10, pady=(10, 0))

        self._status_dot = tk.Label(
            top, text="\u2B24", font=("Segoe UI", 14),
            fg=STATUS_COLORS["stopped"],
        )
        self._status_dot.pack(side="left")

        self._status_label = tk.Label(
            top, text="Starting...",
            font=("Segoe UI", 11, "bold"), anchor="w", padx=8,
        )
        self._status_label.pack(side="left", fill="x", expand=True)

        self._btn_open = tk.Button(
            top, text="Open WebUI", command=self._on_open_webui,
            state=tk.DISABLED, padx=10,
        )
        self._btn_open.pack(side="right", padx=(4, 0))

        self._btn_quit = tk.Button(
            top, text="Stop && Quit", command=self._on_quit, padx=10,
        )
        self._btn_quit.pack(side="right")

        # ── Log area ──
        self._text = scrolledtext.ScrolledText(
            self._root, wrap=tk.WORD,
            font=("Consolas", 9), state=tk.DISABLED,
            bg="#1e1e1e", fg="#cccccc",
            insertbackground="#cccccc", padx=8, pady=8,
        )
        self._text.pack(fill="both", expand=True, padx=10, pady=10)

        # ── Version label ──
        ver = tk.Label(
            self._root, text=f"v{APP_VERSION}",
            font=("Segoe UI", 8), fg="#999999", anchor="e",
        )
        ver.pack(fill="x", padx=12, pady=(0, 6))

    # ── Queue-based thread-safe updates ──────────────────────────────

    def _poll_queue(self):
        """Drain the queue and apply UI updates."""
        try:
            while True:
                action, data = self._queue.get_nowait()
                if action == "log":
                    self._append_log(data)
                elif action == "status":
                    self._set_ui_status(*data)
                elif action == "enable_open":
                    self._btn_open.config(state=tk.NORMAL)
                elif action == "disable_open":
                    self._btn_open.config(state=tk.DISABLED)
        except queue.Empty:
            pass
        self._root.after(100, self._poll_queue)

    def _append_log(self, message):
        self._text.config(state=tk.NORMAL)
        self._text.insert(tk.END, message + "\n")
        self._text.see(tk.END)
        self._text.config(state=tk.DISABLED)

    def _set_ui_status(self, status, detail):
        self._status = status
        color = STATUS_COLORS.get(status, "#808080")
        self._status_dot.config(fg=color)
        label = status.capitalize()
        if detail:
            label += f" — {detail}"
        self._status_label.config(text=label)

    # ── Thread-safe public API (called from background threads) ──────

    def log(self, message):
        logger.info(message)
        self._queue.put(("log", message))

    def set_status(self, status, detail=""):
        self._queue.put(("status", (status, detail)))

    def enable_open_button(self):
        self._queue.put(("enable_open", None))

    def disable_open_button(self):
        self._queue.put(("disable_open", None))

    # ── Button handlers ──────────────────────────────────────────────

    def _on_open_webui(self):
        webbrowser.open(WEBUI_URL)

    def _on_quit(self):
        self._btn_quit.config(state=tk.DISABLED, text="Stopping...")
        thread = threading.Thread(target=self._quit_flow, daemon=True)
        thread.start()

    def _quit_flow(self):
        """Stop containers then exit (runs in background thread)."""
        if self._status == "running":
            self.log("Stopping containers...")
            try:
                docker_manager.stop()
                self.log("Containers stopped.")
            except Exception as e:
                logger.error("Error stopping containers: %s", e)
        # Schedule exit on the main thread
        self._root.after(0, self._root.destroy)

    # ── Startup flow ─────────────────────────────────────────────────

    def _startup_flow(self):
        """Full startup sequence: prerequisites -> pull -> start -> open."""
        first_run = docker_manager.is_first_run()

        if first_run:
            self.log("First-time setup — this may take 10-30 minutes.")
            self.log("Please keep this window open and stay connected to the internet.\n")

        try:
            self.set_status("starting", "Checking prerequisites...")
            self.log("Checking for Docker Desktop...")

            ok, msg = prerequisites.check_prerequisites()
            if not ok:
                self.set_status("error", "Docker not available")
                self.log(f"\n{msg}")
                if "not installed" in msg.lower():
                    prerequisites.open_docker_download_page()
                return
            self.log("Docker Desktop is ready.")

            if first_run:
                self.set_status("starting", "Downloading Docker images...")
                self.log("\nPulling Docker images (this is the largest download)...")

                def on_image_progress(line):
                    self.set_status("starting", "Downloading Docker images...")
                    self.log(line)

                docker_manager.pull_images(on_progress=on_image_progress)
                self.log("Docker images downloaded successfully.\n")

            self.set_status("starting", "Starting containers...")
            self.log("Starting containers...")
            docker_manager.start()
            self.log("Containers started.")

            self.set_status("starting", "Waiting for Ollama...")
            self.log("Waiting for Ollama to be ready...")
            if not docker_manager.wait_for_ollama(timeout=180):
                self.set_status("error", "Ollama not responding")
                self.log("\nOllama failed to start. Check Docker Desktop is running and try again.")
                return
            self.log("Ollama is ready.")

            self.set_status("starting", "Waiting for web interface...")
            self.log("Waiting for web interface to be ready...")
            if not docker_manager.wait_for_webui(timeout=180):
                self.set_status("error", "Web interface not responding")
                self.log("\nThe web interface failed to start. Try restarting the application.")
                return
            self.log("Web interface is ready.")

            if first_run:
                docker_manager.mark_setup_complete()

            self.set_status("running", "")
            self.enable_open_button()
            self.log("\nLocalLLM is running. Opening your browser...")
            webbrowser.open(WEBUI_URL)

        except Exception as e:
            logger.exception("Startup failed")
            self.set_status("error", str(e)[:80])
            self.log(f"\nError: {e}")

    # ── Run ──────────────────────────────────────────────────────────

    def run(self):
        """Build the window, start the startup flow, enter mainloop."""
        self._build()
        self._poll_queue()

        # Start the startup flow in a background thread
        thread = threading.Thread(target=self._startup_flow, daemon=True)
        thread.start()

        self._root.mainloop()
