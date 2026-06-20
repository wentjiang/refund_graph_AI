from __future__ import annotations

from .state import RefundState


def parse_user_intent(state: RefundState) -> None:
    """Node 1: placeholder parser for tags_removed and user_emotion."""
    text = state.user_input.lower()

    tags_keywords = ["剪", "剪掉", "吊牌", "标签", "洗过", "穿过"]
    angry_keywords = ["气死", "愤怒", "太差", "必须", "垃圾"]

    state.tags_removed = any(keyword in text for keyword in tags_keywords)
    state.user_emotion = "angry" if any(keyword in text for keyword in angry_keywords) else "calm"


def risk_policy_check(state: RefundState) -> None:
    """Node 2: hard-coded policy check."""
    if state.item_price > 500 and state.tags_removed is True:
        state.policy_passed = False
    else:
        state.policy_passed = True
        state.refund_amount = state.item_price


def negotiate_customer_care(state: RefundState) -> None:
    """Node 3: fixed compromise strategy for blocked cases."""
    state.refund_amount = state.item_price * 0.3
    state.coupon_issued = True
    state.negotiation_log.append(
        "很抱歉给您带来不便。为尽力弥补，本次可为您安排30%退款并发放20元优惠券。"
    )


def execute_refund(state: RefundState) -> str:
    """Node 4: mock payment API call."""
    return f"[SUCCESS] 已向用户原路退款 ￥{state.refund_amount:.2f} 元"


def generate_final_notification(state: RefundState) -> str:
    """Node 5: plain text closing notification."""
    coupon_text = "并已发放20元优惠券" if state.coupon_issued else "未发放优惠券"
    return (
        f"尊敬的用户，您的退款申请已处理完成。退款金额为￥{state.refund_amount:.2f}，"
        f"{coupon_text}。退款通常将在1-3个工作日原路到账。"
    )


def run_workflow(user_input: str, item_price: float = 600.0) -> tuple[RefundState, list[str]]:
    """Run the full refund DAG flow and return state + output messages."""
    state = RefundState(user_input=user_input, item_price=item_price)
    messages: list[str] = []

    parse_user_intent(state)
    risk_policy_check(state)

    if not state.policy_passed:
        negotiate_customer_care(state)

    messages.append(execute_refund(state))
    messages.append(generate_final_notification(state))

    return state, messages
