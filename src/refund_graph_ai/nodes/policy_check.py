from __future__ import annotations

from ..llm_client import LOGGER, _state_preview
from ..state import WorkflowState


def risk_policy_check(state: WorkflowState) -> WorkflowState:
    """Node 2: hard-coded policy check."""
    LOGGER.debug("node=risk_policy_check start state=%s", _state_preview(state))
    if state["item_price"] > 500 and state["tags_removed"] is True:
        output = {"policy_passed": False}
        LOGGER.debug("node=risk_policy_check end output=%s", output)
        return output

    output = {
        "policy_passed": True,
        "refund_amount": state["item_price"],
    }
    LOGGER.debug("node=risk_policy_check end output=%s", output)
    return output
