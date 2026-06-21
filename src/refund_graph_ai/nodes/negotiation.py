from __future__ import annotations

from ..llm_client import (
    LOGGER,
    _generate_copy_with_llm,
    _merge_error,
    _should_record_error,
    _state_preview,
)
from ..state import WorkflowState


def issue_coupon_tool() -> bool:
    LOGGER.debug("tool=issue_coupon_tool called")
    return True


def negotiate_customer_care(state: WorkflowState) -> WorkflowState:
    """Node 3: code-controlled compensation with LLM-generated copy."""
    LOGGER.debug("node=negotiate_customer_care start state=%s", _state_preview(state))
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
        LOGGER.warning("node=negotiate_customer_care fallback reason=%s", exc)
        if _should_record_error(exc):
            error_msg = _merge_error(state, f"negotiation fallback: {exc}")

    negotiation_log = list(state.get("negotiation_log", []))
    negotiation_log.append(negotiation_text)

    output = {
        "refund_amount": refund_amount,
        "coupon_issued": coupon_issued,
        "negotiation_log": negotiation_log,
        "error_msg": error_msg,
    }
    LOGGER.debug("node=negotiate_customer_care end output=%s", output)
    return output
