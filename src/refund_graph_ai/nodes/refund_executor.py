from __future__ import annotations

from ..llm_client import LOGGER, _state_preview
from ..state import WorkflowState


def execute_refund(state: WorkflowState) -> WorkflowState:
    """Node 4: mock payment API call."""
    LOGGER.debug("node=execute_refund start state=%s", _state_preview(state))
    refund_result = f"[SUCCESS] 已向用户原路退款 ￥{state['refund_amount']:.2f} 元"
    print(refund_result)
    output = {"refund_result": refund_result}
    LOGGER.info("node=execute_refund success result=%s", refund_result)
    return output
