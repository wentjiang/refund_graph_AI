from .workflow import run_workflow


def main() -> None:
    sample_input = "衣服质量太差了，标签我已经剪掉了，必须全款退！"
    state, messages = run_workflow(sample_input)

    print("=== Refund Graph AI Demo ===")
    print(f"policy_passed={state.policy_passed}")
    print(f"refund_amount={state.refund_amount:.2f}")
    print(f"coupon_issued={state.coupon_issued}")
    if state.error_msg:
        print(f"error_msg={state.error_msg}")
    for msg in messages:
        print(msg)


if __name__ == "__main__":
    main()
