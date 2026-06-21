from __future__ import annotations

from ..llm_client import (
    LOGGER,
    _get_chat_model,
    _merge_error,
    _should_record_error,
    _state_preview,
)
from ..state import WorkflowState


class IntentExtractionSchema:
    tags_removed: bool
    user_emotion: str


def _keyword_fallback(user_input: str) -> tuple[bool, str]:
    text = user_input.lower()

    tags_keywords = ["剪掉", "洗过", "穿过"]
    angry_keywords = ["气死", "愤怒", "太差", "必须", "垃圾", "差劲", "失望"]
    calm_keywords = ["麻烦", "谢谢", "可以", "帮我"]

    tags_removed = any(keyword in text for keyword in tags_keywords)
    if any(keyword in text for keyword in angry_keywords):
        user_emotion = "angry"
    elif any(keyword in text for keyword in calm_keywords):
        user_emotion = "calm"
    else:
        user_emotion = "unknown"

    return tags_removed, user_emotion


def _extract_user_intent_via_llm(user_input: str) -> tuple[bool, str]:
    LOGGER.debug("intent llm call start")
    model = _get_chat_model()
    if model is None:
        raise RuntimeError("Ollama model is unavailable")

    structured_model = model.with_structured_output(IntentExtractionSchema)
    result = structured_model.invoke(
        "请从以下退款文本中提取两个字段：tags_removed 和 user_emotion。"
        "tags_removed 表示用户是否提及剪掉标签、洗过、穿过等影响二次销售的行为；"
        "user_emotion 仅返回简洁情绪值，如 angry、calm、sad、unknown。"
        f"文本：{user_input}"
    )

    if isinstance(result, dict):
        LOGGER.debug("intent llm call done with dict result")
        return (
            bool(result.get("tags_removed", False)),
            str(result.get("user_emotion", "unknown")),
        )

    LOGGER.debug("intent llm call done with object result")
    return bool(getattr(result, "tags_removed", False)), str(
        getattr(result, "user_emotion", "unknown")
    )


def parse_user_intent(state: WorkflowState) -> WorkflowState:
    """Node 1: extract tags_removed and user_emotion with an LLM-first fallback."""
    LOGGER.debug("node=parse_user_intent start state=%s", _state_preview(state))
    try:
        tags_removed, user_emotion = _extract_user_intent_via_llm(state["user_input"])
        error_msg = state.get("error_msg", "")
    except Exception as exc:
        tags_removed, user_emotion = _keyword_fallback(state["user_input"])
        error_msg = state.get("error_msg", "")
        LOGGER.warning("node=parse_user_intent fallback reason=%s", exc)
        if _should_record_error(exc):
            error_msg = _merge_error(state, f"intent parsing fallback: {exc}")

    output = {
        "tags_removed": tags_removed,
        "user_emotion": user_emotion,
        "error_msg": error_msg,
    }
    LOGGER.debug("node=parse_user_intent end output=%s", output)
    return output
