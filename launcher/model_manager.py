import json
import logging
import urllib.request
import urllib.error

from launcher.config import OLLAMA_API_BASE, DEFAULT_MODELS

logger = logging.getLogger(__name__)


def list_models():
    """Return the list of models currently available in Ollama."""
    url = f"{OLLAMA_API_BASE}/api/tags"
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            return [m["name"] for m in data.get("models", [])]
    except (urllib.error.URLError, OSError, json.JSONDecodeError) as e:
        logger.error("Failed to list models: %s", e)
        return []


def pull_model(model_name, on_progress=None):
    """Pull a single model via the Ollama API.

    Args:
        model_name: The model identifier (e.g. "llama3.2:3b").
        on_progress: Optional callback(model_name, status, completed, total)
            where completed/total are byte counts (may be 0 if unknown).

    Raises:
        RuntimeError: If the pull fails.
    """
    url = f"{OLLAMA_API_BASE}/api/pull"
    payload = json.dumps({"name": model_name, "stream": True}).encode()
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    logger.info("Pulling model: %s", model_name)
    try:
        with urllib.request.urlopen(req, timeout=3600) as resp:
            for line in resp:
                line = line.decode().strip()
                if not line:
                    continue
                try:
                    msg = json.loads(line)
                except json.JSONDecodeError:
                    continue

                status = msg.get("status", "")
                completed = msg.get("completed", 0)
                total = msg.get("total", 0)

                if on_progress:
                    on_progress(model_name, status, completed, total)

                if "error" in msg:
                    raise RuntimeError(f"Ollama error pulling {model_name}: {msg['error']}")

    except urllib.error.URLError as e:
        raise RuntimeError(f"Failed to connect to Ollama API: {e}")

    logger.info("Model %s pulled successfully", model_name)


def pull_default_models(on_progress=None):
    """Pull all models in the DEFAULT_MODELS list.

    Args:
        on_progress: Optional callback(model_name, status, completed, total).

    Returns:
        List of model names that were successfully pulled.
    """
    existing = list_models()
    pulled = []

    for model_name in DEFAULT_MODELS:
        # Check if model is already available (handles both "name" and "name:tag" formats)
        if any(model_name in existing_name or existing_name.startswith(model_name.split(":")[0])
               for existing_name in existing):
            logger.info("Model %s already available, skipping", model_name)
            pulled.append(model_name)
            continue

        try:
            pull_model(model_name, on_progress=on_progress)
            pulled.append(model_name)
        except RuntimeError as e:
            logger.error("Failed to pull model %s: %s", model_name, e)

    return pulled
