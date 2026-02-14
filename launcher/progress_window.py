"""A tkinter-based progress window for showing setup progress to the user.

The window runs in its own thread and accepts log messages via a
thread-safe queue, so it can be driven from the tray app's startup flow
without blocking.
"""

import queue
import threading
import tkinter as tk
from tkinter import scrolledtext

from launcher.config import APP_NAME


class ProgressWindow:
    """A simple window that displays log messages during setup."""

    def __init__(self, title=f"{APP_NAME} — Setting up"):
        self._title = title
        self._queue = queue.Queue()
        self._thread = None
        self._ready = threading.Event()
        self._root = None

    def show(self):
        """Open the progress window in a background thread.

        Blocks briefly until the window is created and visible.
        """
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        self._ready.wait(timeout=5)

    def _run(self):
        """Build and run the tkinter window (runs in its own thread)."""
        self._root = tk.Tk()
        self._root.title(self._title)
        self._root.geometry("620x380")
        self._root.resizable(True, True)

        # Status label at the top
        self._status_label = tk.Label(
            self._root,
            text="Starting up...",
            font=("Segoe UI", 11, "bold"),
            anchor="w",
            padx=10,
            pady=8,
        )
        self._status_label.pack(fill="x")

        # Scrollable log area
        self._text = scrolledtext.ScrolledText(
            self._root,
            wrap=tk.WORD,
            font=("Consolas", 9),
            state=tk.DISABLED,
            bg="#1e1e1e",
            fg="#cccccc",
            insertbackground="#cccccc",
            padx=8,
            pady=8,
        )
        self._text.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Prevent the user from closing the window during setup
        self._root.protocol("WM_DELETE_WINDOW", self._on_close_attempt)

        self._ready.set()
        self._poll_queue()
        self._root.mainloop()

    def _on_close_attempt(self):
        """Ignore close button clicks — the window closes when setup is done."""
        pass

    def _poll_queue(self):
        """Process queued messages from other threads."""
        try:
            while True:
                action, data = self._queue.get_nowait()
                if action == "log":
                    self._append_log(data)
                elif action == "status":
                    self._status_label.config(text=data)
                elif action == "close":
                    self._root.destroy()
                    return
                elif action == "error":
                    self._status_label.config(text=data, fg="#ff4444")
                    # Re-enable close button on error so user can dismiss
                    self._root.protocol("WM_DELETE_WINDOW", self._root.destroy)
        except queue.Empty:
            pass
        if self._root:
            self._root.after(100, self._poll_queue)

    def _append_log(self, message):
        """Append a line to the log text area."""
        self._text.config(state=tk.NORMAL)
        self._text.insert(tk.END, message + "\n")
        self._text.see(tk.END)
        self._text.config(state=tk.DISABLED)

    # ── Public API (thread-safe, called from other threads) ──────────

    def log(self, message):
        """Append a log line to the window."""
        self._queue.put(("log", message))

    def set_status(self, message):
        """Update the bold status label at the top of the window."""
        self._queue.put(("status", message))

    def set_error(self, message):
        """Set an error status and allow the user to close the window."""
        self._queue.put(("error", message))

    def close(self):
        """Close the progress window."""
        self._queue.put(("close", None))
