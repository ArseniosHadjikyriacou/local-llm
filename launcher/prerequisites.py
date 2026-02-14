import shutil
import subprocess
import time
import logging
import webbrowser

logger = logging.getLogger(__name__)

DOCKER_DESKTOP_DOWNLOAD_URL = "https://www.docker.com/products/docker-desktop/"


def is_docker_installed():
    """Check if the docker CLI is available on PATH."""
    return shutil.which("docker") is not None


def is_docker_running():
    """Check if the Docker daemon is responsive."""
    try:
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            timeout=10,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def start_docker_desktop():
    """Attempt to start Docker Desktop on Windows."""
    docker_desktop_paths = [
        r"C:\Program Files\Docker\Docker\Docker Desktop.exe",
        r"C:\Program Files (x86)\Docker\Docker\Docker Desktop.exe",
    ]
    for path in docker_desktop_paths:
        try:
            subprocess.Popen([path], creationflags=subprocess.DETACHED_PROCESS)
            logger.info("Started Docker Desktop from %s", path)
            return True
        except FileNotFoundError:
            continue
    logger.warning("Could not find Docker Desktop executable")
    return False


def wait_for_docker(timeout=120, poll_interval=3):
    """Wait for the Docker daemon to become responsive.

    Returns True if Docker is ready, False if timed out.
    """
    start = time.time()
    while time.time() - start < timeout:
        if is_docker_running():
            return True
        time.sleep(poll_interval)
    return False


def open_docker_download_page():
    """Open the Docker Desktop download page in the default browser."""
    webbrowser.open(DOCKER_DESKTOP_DOWNLOAD_URL)


def check_prerequisites():
    """Check all prerequisites and return (ok, message).

    Returns:
        (True, "") if everything is ready.
        (False, description) if something is missing or not running.
    """
    if not is_docker_installed():
        return False, (
            "Docker Desktop is not installed.\n\n"
            "Please install Docker Desktop from:\n"
            f"{DOCKER_DESKTOP_DOWNLOAD_URL}\n\n"
            "After installation, restart this application."
        )

    if not is_docker_running():
        logger.info("Docker is installed but not running. Attempting to start...")
        started = start_docker_desktop()
        if not started:
            return False, (
                "Docker Desktop is installed but could not be started automatically.\n"
                "Please start Docker Desktop manually and then restart this application."
            )
        logger.info("Waiting for Docker daemon to become ready...")
        if not wait_for_docker():
            return False, (
                "Docker Desktop is starting but taking too long.\n"
                "Please wait for Docker Desktop to fully start, then restart this application."
            )

    return True, ""
