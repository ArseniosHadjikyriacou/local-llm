import os
import sys

APP_NAME = "LocalLLM"
APP_VERSION = "1.0.0"

# Ports (must match .env / docker-compose.yml)
OPEN_WEBUI_PORT = 3000
OLLAMA_PORT = 11434

OLLAMA_API_BASE = f"http://localhost:{OLLAMA_PORT}"
WEBUI_URL = f"http://localhost:{OPEN_WEBUI_PORT}"


def get_app_dir():
    """Return the application directory (where the .exe or script lives)."""
    if getattr(sys, "frozen", False):
        # Running as PyInstaller bundle
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_data_dir():
    """Return a persistent data directory for marker files and logs."""
    data_dir = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), APP_NAME)
    os.makedirs(data_dir, exist_ok=True)
    return data_dir


def get_compose_file():
    """Return the path to docker-compose.yml."""
    return os.path.join(get_app_dir(), "docker-compose.yml")


def get_env_file():
    """Return the path to .env."""
    return os.path.join(get_app_dir(), ".env")


FIRST_RUN_MARKER = os.path.join(get_data_dir(), ".setup_complete")
