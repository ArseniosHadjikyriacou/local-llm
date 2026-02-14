import subprocess
import time
import logging
import urllib.request
import urllib.error

from launcher.config import (
    get_compose_file,
    get_app_dir,
    OLLAMA_API_BASE,
    FIRST_RUN_MARKER,
)

logger = logging.getLogger(__name__)


def _compose_cmd(*args):
    """Build a docker compose command list."""
    compose_file = get_compose_file()
    return ["docker", "compose", "-f", compose_file, *args]


def _run(cmd, **kwargs):
    """Run a command and return the CompletedProcess."""
    logger.info("Running: %s", " ".join(cmd))
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=get_app_dir(),
        **kwargs,
    )


def is_first_run():
    """Check if this is the first time the app has been launched."""
    import os
    return not os.path.exists(FIRST_RUN_MARKER)


def mark_setup_complete():
    """Write the marker file indicating first-run setup is done."""
    with open(FIRST_RUN_MARKER, "w") as f:
        f.write("setup_complete")
    logger.info("First-run setup marked as complete")


def pull_images(on_progress=None):
    """Pull Docker images via docker compose pull.

    Args:
        on_progress: Optional callback(line: str) for progress updates.
    """
    logger.info("Pulling Docker images...")
    process = subprocess.Popen(
        _compose_cmd("pull"),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        cwd=get_app_dir(),
    )
    for line in iter(process.stdout.readline, ""):
        line = line.strip()
        if line:
            logger.info("pull: %s", line)
            if on_progress:
                on_progress(line)
    process.wait()
    if process.returncode != 0:
        raise RuntimeError("Failed to pull Docker images")
    logger.info("Docker images pulled successfully")


def start():
    """Start the Docker Compose stack."""
    logger.info("Starting compose stack...")
    result = _run(_compose_cmd("up", "-d"))
    if result.returncode != 0:
        logger.error("Failed to start: %s", result.stderr)
        raise RuntimeError(f"Failed to start containers: {result.stderr}")
    logger.info("Compose stack started")


def stop():
    """Stop the Docker Compose stack."""
    logger.info("Stopping compose stack...")
    result = _run(_compose_cmd("down"))
    if result.returncode != 0:
        logger.error("Failed to stop: %s", result.stderr)
        raise RuntimeError(f"Failed to stop containers: {result.stderr}")
    logger.info("Compose stack stopped")


def status():
    """Check if containers are running.

    Returns:
        dict with keys 'ollama' and 'webui', values are True/False.
    """
    result = _run(_compose_cmd("ps", "--format", "{{.Name}} {{.State}}"))
    lines = result.stdout.strip().splitlines() if result.returncode == 0 else []

    running = {}
    for line in lines:
        parts = line.split()
        if len(parts) >= 2:
            name, state = parts[0], parts[1]
            running[name] = state.lower() == "running"

    return {
        "ollama": running.get("localllm-ollama", False),
        "webui": running.get("localllm-webui", False),
    }


def is_running():
    """Return True if both containers are running."""
    s = status()
    return s.get("ollama", False) and s.get("webui", False)


def wait_for_ollama(timeout=120, poll_interval=3):
    """Wait for the Ollama API to become responsive.

    Returns True if responsive, False if timed out.
    """
    url = f"{OLLAMA_API_BASE}/api/tags"
    start = time.time()
    while time.time() - start < timeout:
        try:
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=5):
                logger.info("Ollama API is responsive")
                return True
        except (urllib.error.URLError, OSError):
            pass
        time.sleep(poll_interval)
    logger.warning("Timed out waiting for Ollama API")
    return False


def wait_for_webui(timeout=120, poll_interval=3):
    """Wait for the Open WebUI to become responsive.

    Returns True if responsive, False if timed out.
    """
    from launcher.config import WEBUI_URL
    start = time.time()
    while time.time() - start < timeout:
        try:
            req = urllib.request.Request(WEBUI_URL, method="GET")
            with urllib.request.urlopen(req, timeout=5):
                logger.info("Open WebUI is responsive")
                return True
        except (urllib.error.URLError, OSError):
            pass
        time.sleep(poll_interval)
    logger.warning("Timed out waiting for Open WebUI")
    return False
