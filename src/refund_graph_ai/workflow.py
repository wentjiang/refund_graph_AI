from __future__ import annotations

from typing import Any

from langgraph.graph import END, StateGraph

try:
    from langchain_ollama import ChatOllama
except ImportError:  # pragma: no cover - dependency is installed in normal runs
    ChatOllama = None  # type: ignore[assignment]

from .state import RefundState, WorkflowState, build_initial_state, refund_state_from_workflow_state

OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "qwen"


class IntentExtractionSchema:
    tags_removed: bool
    user_emotion: str


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


def _get_chat_model() -> Any:
    if ChatOllama is None:
        return None

    try:
        return ChatOllama(model=OLLAMA_MODEL, base_url=OLLAMA_BASE_URL, temperature=0)
    except Exception:
        return None


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
        return bool(result.get("tags_removed", False)), str(result.get("user_emotion", "unknown"))

    return bool(getattr(result, "tags_removed", False)), str(
        getattr(result, "user_emotion", "unknown")
    )


def _generate_copy_with_llm(prompt: str) -> str:
    model = _get_chat_model()
    if model is None:
        raise RuntimeError("Ollama model is unavailable")

    response = model.invoke(prompt)
    content = getattr(response, "content", "")
    if not content:
        raise RuntimeError("Empty model response")

    return str(content).strip()


def parse_user_intent(state: WorkflowState) -> WorkflowState:
    """Node 1: extract tags_removed and user_emotion with an LLM-first fallback."""
    try:
        tags_removed, user_emotion = _extract_user_intent_via_llm(state["user_input"])
        error_msg = state.get("error_msg", "")
    except Exception as exc:
        tags_removed, user_emotion = _keyword_fallback(state["user_input"])
        error_msg = state.get("error_msg", "")
        if _should_record_error(exc):
            error_msg = _merge_error(state, f"intent parsing fallback: {exc}")

    return {
        "tags_removed": tags_removed,
        "user_emotion": user_emotion,
        "error_msg": error_msg,
    }


def risk_policy_check(state: WorkflowState) -> WorkflowState:
    """Node 2: hard-coded policy check."""
    if state["item_price"] > 500 and state["tags_removed"] is True:
        return {"policy_passed": False}

    return {
        "policy_passed": True,
        "refund_amount": state["item_price"],
    }


def issue_coupon_tool() -> bool:
    return True


def negotiate_customer_care(state: WorkflowState) -> WorkflowState:
    """Node 3: code-controlled compensation with LLM-generated copy."""
    refund_amount = round(state["item_price"] * 0.3, 2)
    coupon_issued = issue_coupon_tool()

    fallback_message = "很抱歉给您带来不便，我们可以为您安排 30% 退款并发放 20 元优惠券。"
    prompt = (
        "你是资深售后公关专家，语气必须极度温柔、充满同理心。"
        "请用一段简洁中文安抚用户，并明确提出固定方案：30% 部分退款 + 20 元优惠券。"
        f"用户情绪：{state.get('user_emotion', 'unknown')}。"
        f"用户原始诉求：{state['user_input']}"
    )

    try:
        negotiation_text = _generate_copy_with_llm(prompt)
        error_msg = state.get("error_msg", "")
    except Exception as exc:
        negotiation_text = fallback_message
        error_msg = state.get("error_msg", "")
        if _should_record_error(exc):
            error_msg = _merge_error(state, f"negotiation fallback: {exc}")

    negotiation_log = list(state.get("negotiation_log", []))
    negotiation_log.append(negotiation_text)

    return {
        "refund_amount": refund_amount,
        "coupon_issued": coupon_issued,
        "negotiation_log": negotiation_log,
        "error_msg": error_msg,
    }


def execute_refund(state: WorkflowState) -> WorkflowState:
    """Node 4: mock payment API call."""
    refund_result = f"[SUCCESS] 已向用户原路退款 ￥{state['refund_amount']:.2f} 元"
    print(refund_result)
    return {"refund_result": refund_result}


def generate_final_notification(state: WorkflowState) -> WorkflowState:
    """Node 5: generate the final closure message with a fallback template."""
    coupon_text = "并已发放20元优惠券" if state.get("coupon_issued", False) else "未发放优惠券"
    fallback_text = (
        f"尊敬的用户，您的退款申请已处理完成。退款金额为￥{state['refund_amount']:.2f}，"
        f"{coupon_text}。退款通常将在1-3个工作日原路到账。"
    )
    prompt = (
        "根据最终的退款金额和优惠券状态，生成一封正式的结案通知。"
        f"退款金额：{state['refund_amount']:.2f}。"
        f"优惠券状态：{'已发放' if state.get('coupon_issued', False) else '未发放'}。"
        "要求措辞得体，说明到账时间和优惠券使用方式。"
    )

    try:
        final_notification = _generate_copy_with_llm(prompt)
        error_msg = state.get("error_msg", "")
    except Exception as exc:
        final_notification = fallback_text
        error_msg = state.get("error_msg", "")
        if _should_record_error(exc):
            error_msg = _merge_error(state, f"final notification fallback: {exc}")

    return {
        "final_notification": final_notification,
        "error_msg": error_msg,
    }


def _route_after_policy(state: WorkflowState) -> str:
    return "negotiate_customer_care" if not state["policy_passed"] else "execute_refund"


def _build_graph() -> Any:
    graph = StateGraph(WorkflowState)
    graph.add_node("parse_user_intent", parse_user_intent)
    graph.add_node("risk_policy_check", risk_policy_check)
    graph.add_node("negotiate_customer_care", negotiate_customer_care)
    graph.add_node("execute_refund", execute_refund)
    graph.add_node("generate_final_notification", generate_final_notification)

    graph.set_entry_point("parse_user_intent")
    graph.add_edge("parse_user_intent", "risk_policy_check")
    graph.add_conditional_edges(
        "risk_policy_check",
        _route_after_policy,
        {
            "negotiate_customer_care": "negotiate_customer_care",
            "execute_refund": "execute_refund",
        },
    )
    graph.add_edge("negotiate_customer_care", "execute_refund")
    graph.add_edge("execute_refund", "generate_final_notification")
    graph.add_edge("generate_final_notification", END)

    return graph.compile()


WORKFLOW_GRAPH = _build_graph()


def run_workflow(user_input: str, item_price: float = 600.0) -> tuple[RefundState, list[str]]:
    """Run the refund workflow and return the finalized state plus visible messages."""
    final_state = WORKFLOW_GRAPH.invoke(build_initial_state(user_input, item_price))
    state = refund_state_from_workflow_state(final_state)

    messages: list[str] = []
    messages.extend(state.negotiation_log)
    if state.refund_result:
        messages.append(state.refund_result)
    if state.final_notification:
        messages.append(state.final_notification)

    return state, messages
