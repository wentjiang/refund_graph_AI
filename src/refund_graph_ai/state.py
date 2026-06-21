from __future__ import annotations

from dataclasses import dataclass, field
from typing import TypedDict


class WorkflowState(TypedDict, total=False):
    user_input: str
    item_price: float
    tags_removed: bool
    user_emotion: str
    policy_passed: bool
    refund_amount: float
    coupon_issued: bool
    negotiation_log: list[str]
    final_notification: str
    refund_result: str
    error_msg: str


@dataclass
class RefundState:
    """Global shared state across workflow nodes."""

    user_input: str
    item_price: float = 600.0
    tags_removed: bool = False
    user_emotion: str = "unknown"
    policy_passed: bool = False
    refund_amount: float = 0.0
    coupon_issued: bool = False
    negotiation_log: list[str] = field(default_factory=list)
    final_notification: str = ""
    refund_result: str = ""
    error_msg: str = ""


def build_initial_state(user_input: str, item_price: float = 600.0) -> WorkflowState:
    return {
        "user_input": user_input,
        "item_price": item_price,
        "tags_removed": False,
        "user_emotion": "unknown",
        "policy_passed": False,
        "refund_amount": 0.0,
        "coupon_issued": False,
        "negotiation_log": [],
        "final_notification": "",
        "refund_result": "",
        "error_msg": "",
    }


def refund_state_from_workflow_state(state: WorkflowState) -> RefundState:
    return RefundState(
        user_input=state.get("user_input", ""),
        item_price=state.get("item_price", 600.0),
        tags_removed=state.get("tags_removed", False),
        user_emotion=state.get("user_emotion", "unknown"),
        policy_passed=state.get("policy_passed", False),
        refund_amount=state.get("refund_amount", 0.0),
        coupon_issued=state.get("coupon_issued", False),
        negotiation_log=list(state.get("negotiation_log", [])),
        final_notification=state.get("final_notification", ""),
        refund_result=state.get("refund_result", ""),
        error_msg=state.get("error_msg", ""),
    )
