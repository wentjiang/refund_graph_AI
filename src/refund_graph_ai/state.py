from dataclasses import dataclass, field


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
