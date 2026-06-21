from __future__ import annotations

from typing import Any

from langgraph.graph import END, StateGraph

from .llm_client import LOGGER, _refresh_log_level, _state_preview, _truncate_text
from .nodes import (
    execute_refund,
    generate_final_notification,
    negotiate_customer_care,
    parse_user_intent,
    risk_policy_check,
)
from .state import (
    RefundState,
    WorkflowState,
    build_initial_state,
    refund_state_from_workflow_state,
)


def _route_after_policy(state: WorkflowState) -> str:
    route = "negotiate_customer_care" if not state["policy_passed"] else "execute_refund"
    LOGGER.debug("routing after risk_policy_check route=%s", route)
    return route


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
    _refresh_log_level()
    LOGGER.debug(
        "workflow start user_input=%s item_price=%.2f",
        _truncate_text(user_input),
        item_price,
    )

    final_state = WORKFLOW_GRAPH.invoke(build_initial_state(user_input, item_price))
    state = refund_state_from_workflow_state(final_state)

    messages: list[str] = []
    messages.extend(state.negotiation_log)
    if state.refund_result:
        messages.append(state.refund_result)
    if state.final_notification:
        messages.append(state.final_notification)

    LOGGER.debug(
        "workflow end state_summary=%s messages_count=%d",
        _state_preview(final_state),
        len(messages),
    )

    return state, messages
