from refund_graph_ai.workflow import run_workflow


def test_full_refund_path() -> None:
    user_input = "衣服收到了，尺码拍小了，我没试穿，吊牌都在，帮我退了吧。"
    state, _ = run_workflow(user_input=user_input, item_price=600.0)

    assert state.policy_passed is True
    assert state.refund_amount == 600.0
    assert state.coupon_issued is False


def test_negotiation_path() -> None:
    user_input = "衣服质量太差了，我气死了，标签我已经剪掉扔了，必须退全款。"
    state, _ = run_workflow(user_input=user_input, item_price=600.0)

    assert state.policy_passed is False
    assert state.refund_amount == 180.0
    assert state.coupon_issued is True
