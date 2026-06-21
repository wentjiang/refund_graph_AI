from refund_graph_ai.main import main_interactive
from refund_graph_ai.state import RefundState


def test_main_interactive_uses_user_input(monkeypatch, capsys) -> None:
    from refund_graph_ai import main as main_module

    captured: dict[str, object] = {}

    def fake_run_workflow(user_input: str, item_price: float = 600.0):
        captured["user_input"] = user_input
        captured["item_price"] = item_price
        state = RefundState(
            user_input=user_input,
            item_price=item_price,
            policy_passed=True,
            refund_amount=item_price,
            coupon_issued=False,
            refund_result=f"[SUCCESS] 已向用户原路退款 ￥{item_price:.2f} 元",
            final_notification="通知文本",
        )
        return state, [state.refund_result, state.final_notification]

    inputs = iter(["我要退货", "666"])
    monkeypatch.setattr(main_module, "run_workflow", fake_run_workflow)
    monkeypatch.setattr("builtins.input", lambda _prompt: next(inputs))

    main_interactive()

    output = capsys.readouterr().out
    assert captured["user_input"] == "我要退货"
    assert captured["item_price"] == 666.0
    assert "policy_passed=True" in output
    assert "refund_amount=666.00" in output
