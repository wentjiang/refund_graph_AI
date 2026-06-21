from .workflow import run_workflow


def _print_result(state, messages: list[str]) -> None:
    print("=== Refund Graph AI Demo ===")
    print(f"policy_passed={state.policy_passed}")
    print(f"refund_amount={state.refund_amount:.2f}")
    print(f"coupon_issued={state.coupon_issued}")
    if state.error_msg:
        print(f"error_msg={state.error_msg}")
    for msg in messages:
        print(msg)


def main() -> None:
    sample_input = "衣服质量太差了，标签我已经剪掉了，必须全款退！"
    state, messages = run_workflow(sample_input)
    _print_result(state, messages)


def main_interactive() -> None:
    print("=== Refund Graph AI Interactive Mode ===")

    try:
        user_input = input("请输入用户退款描述: ").strip()
        if not user_input:
            print("输入为空，已取消运行。")
            return

        price_input = input("请输入商品价格（直接回车默认 600）: ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\n已取消运行。")
        return

    item_price = 600.0
    if price_input:
        try:
            item_price = float(price_input)
        except ValueError:
            print("价格输入无效，已使用默认价格 600。")

    state, messages = run_workflow(user_input=user_input, item_price=item_price)
    _print_result(state, messages)


if __name__ == "__main__":
    main()
