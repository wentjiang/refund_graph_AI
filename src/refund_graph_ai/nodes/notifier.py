from __future__ import annotations

from ..llm_client import (
    LOGGER,
    _generate_copy_with_llm,
    _merge_error,
    _should_record_error,
    _state_preview,
)
from ..state import WorkflowState


def generate_final_notification(state: WorkflowState) -> WorkflowState:
    """Node 5: generate the final closure message with a fallback template."""
    LOGGER.debug("node=generate_final_notification start state=%s", _state_preview(state))
    coupon_text = "并已发放20元优惠券" if state.get("coupon_issued", False) else "未发放优惠券"
    fallback_text = (
        f"尊敬的用户，您的退款申请已处理完成。退款金额为￥{state['refund_amount']:.2f}，"
        f"{coupon_text}。退款通常将在1-3个工作日原路到账。"
    )
    prompt = (
        "根据最终的退款金额和优惠券状态，生成一封正式的结案通知。"
        f"退款金额：{state['refund_amount']:.2f}。"
        f"优惠券状态：{'已发放' if state.get('coupon_issued', False) else '未发放'}。"
        "要求措辞得体，说明到账时间和优惠券使用方式。内容长度不能太长, 不能显得啰嗦"
    )

    try:
        final_notification = _generate_copy_with_llm(prompt)
        error_msg = state.get("error_msg", "")
    except Exception as exc:
        final_notification = fallback_text
        error_msg = state.get("error_msg", "")
        LOGGER.warning("node=generate_final_notification fallback reason=%s", exc)
        if _should_record_error(exc):
            error_msg = _merge_error(state, f"final notification fallback: {exc}")

    output = {
        "final_notification": final_notification,
        "error_msg": error_msg,
    }
    LOGGER.debug("node=generate_final_notification end output=%s", output)
    return output
