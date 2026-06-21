from __future__ import annotations

import json
import logging
import os
from typing import Any
from urllib import error, request

try:
    import colorlog
except ImportError:  # pragma: no cover - for minimal installations
    colorlog = None  # type: ignore[assignment]

try:
    from langchain_ollama import ChatOllama
except ImportError:  # pragma: no cover - installed in normal runs
    ChatOllama = None  # type: ignore[assignment]

from .state import WorkflowState

OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "qwen3:8b"

LOGGER = logging.getLogger("refund_graph_ai.workflow")

if not LOGGER.handlers:
    _handler = logging.StreamHandler()
    if colorlog:
        _formatter = colorlog.ColoredFormatter(
            "%(log_color)s%(asctime)s %(levelname)-8s %(name)s%(reset)s - %(message)s",
            log_colors={
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "red,bg_white",
            },
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    else:
        _formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s - %(message)s")
    _handler.setFormatter(_formatter)
    LOGGER.addHandler(_handler)
    LOGGER.propagate = False


def _refresh_log_level() -> None:
    level_name = os.getenv("REFUND_GRAPH_AI_LOG_LEVEL", "WARNING").upper()
    level = getattr(logging, level_name, logging.WARNING)
    LOGGER.setLevel(level)


def _truncate_text(value: str, limit: int = 80) -> str:
    if len(value) <= limit:
        return value
    return f"{value[:limit]}..."


def _state_preview(state: WorkflowState) -> dict[str, Any]:
    return {
        "user_input": _truncate_text(str(state.get("user_input", ""))),
        "item_price": state.get("item_price"),
        "tags_removed": state.get("tags_removed"),
        "user_emotion": state.get("user_emotion"),
        "policy_passed": state.get("policy_passed"),
        "refund_amount": state.get("refund_amount"),
        "coupon_issued": state.get("coupon_issued"),
        "negotiation_log_size": len(state.get("negotiation_log", [])),
        "has_error": bool(state.get("error_msg", "")),
    }


def _merge_error(state: WorkflowState, message: str) -> str:
    existing_message = state.get("error_msg", "")
    if not existing_message:
        return message
    return f"{existing_message}; {message}"


def _should_record_error(exc: Exception) -> bool:
    message = str(exc).lower()
    expected_offline_markers = [
        "model 'qwen' not found",
        "ollama model is unavailable",
        "404",
        "validation errors for chatrequest",
    ]
    return not any(marker in message for marker in expected_offline_markers)


def _fetch_ollama_json(path: str) -> dict[str, Any] | None:
    url = f"{OLLAMA_BASE_URL}{path}"
    try:
        with request.urlopen(url, timeout=2.5) as response:  # nosec B310
            payload = response.read().decode("utf-8")
            return json.loads(payload)
    except error.URLError as exc:
        LOGGER.warning("ollama request failed url=%s reason=%s", url, exc)
    except TimeoutError:
        LOGGER.warning("ollama request timeout url=%s", url)
    except Exception as exc:
        LOGGER.warning("unexpected ollama request error url=%s reason=%s", url, exc)
    return None


def _log_ollama_diagnostics() -> None:
    tags = _fetch_ollama_json("/api/tags")
    if tags is None:
        LOGGER.error(
            "cannot reach Ollama at %s. "
            "Check: 1) `ollama serve` 2) local firewall/port 11434",
            OLLAMA_BASE_URL,
        )
        return

    models: list[str] = []
    for model_info in tags.get("models", []):
        name = model_info.get("name")
        if isinstance(name, str):
            models.append(name)

    LOGGER.debug("ollama reachable with %d local model(s): %s", len(models), models)

    if OLLAMA_MODEL not in models:
        LOGGER.error(
            "configured model `%s` not found locally. Available models=%s. "
            "Suggestion: `ollama pull %s`",
            OLLAMA_MODEL,
            models,
            OLLAMA_MODEL,
        )


def _get_chat_model() -> Any:
    if ChatOllama is None:
        LOGGER.error(
            "ChatOllama import failed. Run `poetry install` and ensure "
            "langchain-ollama is installed."
        )
        return None

    _log_ollama_diagnostics()

    try:
        LOGGER.debug(
            "creating ChatOllama client base_url=%s model=%s temperature=0",
            OLLAMA_BASE_URL,
            OLLAMA_MODEL,
        )
        return ChatOllama(model=OLLAMA_MODEL, base_url=OLLAMA_BASE_URL, temperature=0)
    except Exception as exc:
        LOGGER.error("failed to create ChatOllama client: %s", exc)
        return None


def _generate_copy_with_llm(prompt: str) -> str:
    LOGGER.debug("copy llm call start, prompt=%s", _truncate_text(prompt, 120))
    model = _get_chat_model()
    if model is None:
        raise RuntimeError("Ollama model is unavailable")

    response = model.invoke(prompt)
    content = getattr(response, "content", "")
    if not content:
        raise RuntimeError("Empty model response")

    LOGGER.debug("copy llm call done")
    return str(content).strip()
