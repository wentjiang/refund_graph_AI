from refund_graph_ai.workflow import run_workflow


def test_full_refund_path() -> None:
    user_input = "衣服收到了，尺码拍小了，我没试穿，吊牌都在，帮我退了吧。"
    state, _ = run_workflow(user_input=user_input, item_price=600.0)

    assert state.policy_passed is True
    assert state.refund_amount == 600.0
    assert state.coupon_issued is False
    assert state.final_notification
    assert state.refund_result == "[SUCCESS] 已向用户原路退款 ￥600.00 元"
    assert state.error_msg == ""


def test_negotiation_path() -> None:
    user_input = "衣服质量太差了，我气死了，标签我已经剪掉扔了，必须退全款。"
    state, _ = run_workflow(user_input=user_input, item_price=600.0)

    assert state.policy_passed is False
    assert state.refund_amount == 180.0
    assert state.coupon_issued is True
    assert state.final_notification
    assert state.refund_result == "[SUCCESS] 已向用户原路退款 ￥180.00 元"


def test_intent_parse_failure_falls_back_and_continues(monkeypatch) -> None:
    from refund_graph_ai import workflow

    def raise_failure(_: str) -> tuple[bool, str]:
        raise RuntimeError("forced intent failure")

    monkeypatch.setattr(workflow, "_extract_user_intent_via_llm", raise_failure)

    user_input = "衣服质量太差了，标签我已经剪掉了，必须全款退！"
    state, messages = run_workflow(user_input=user_input, item_price=600.0)

    assert state.policy_passed is False
    assert state.refund_amount == 180.0
    assert state.coupon_issued is True
    assert state.error_msg
    assert state.final_notification
    assert len(messages) >= 2
