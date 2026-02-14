"""LocalLLM Launcher — entry point.

Starts a control window that manages the Ollama + Open WebUI
Docker Compose stack.
"""

import logging
import sys

from launcher.config import APP_NAME, get_data_dir


def setup_logging():
    """Configure logging to file and stderr."""
    import os
    log_file = os.path.join(get_data_dir(), "launcher.log")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stderr),
        ],
    )


def main():
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting %s launcher", APP_NAME)

    from launcher.app_window import AppWindow
    app = AppWindow()
    app.run()


if __name__ == "__main__":
    main()
