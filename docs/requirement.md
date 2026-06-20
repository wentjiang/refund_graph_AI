# 项目需求文档：AI 混合动力售后退款专家 (Practice Project)

## 1. 项目概述

本项目旨在实现一个线上客服售后退款系统。系统需要接收用户用自然语言输入的退款申请，通过 AI 提取关键信息，结合业务硬性规则（代码）进行风控。在不符合全额退款条件时，由 AI 扮演谈判专家与用户协商（提供部分退款 + 优惠券方案），最终安全地执行退款并通知用户。

## 2. 全局状态定义 (State)

在图结构中，所有节点共享一个全局状态对象。请定义一个 `RefundState` 类（或字典），包含以下字段：

| 字段名 | 类型 | 说明 | 写入节点 |
| --- | --- | --- | --- |
| `user_input` | String | 用户原始输入的投诉/退款文本 | 系统入口 |
| `item_price` | Float | 商品原价（假设本单固定为 600 元） | 系统初始化 |
| `tags_removed` | Boolean | 衣服标签是否已被剪掉（AI 提取） | 意图解析节点 |
| `user_emotion` | String | 用户情绪（如：愤怒、平静、失望） | 意图解析节点 |
| `policy_passed` | Boolean | 是否通过硬性风控合规校验 | 风控校验节点 |
| `refund_amount` | Float | 最终决定的退款金额 | 谈判节点或风控节点 |
| `coupon_issued` | Boolean | 是否发放了补偿优惠券 | 谈判节点 |
| `negotiation_log` | List | 谈判节点的对话历史（用于多轮对话） | 谈判节点 |

## 3. 工作流拓扑图 (Topology)

系统采用有向无环图（DAG）结构，流程如下：

```text
[Start] --> 1. 用户意图解析 (Agent)
                --> 2. 风控与策略校验 (Code)
                         |- (符合政策) --> 4. 执行退款 API (Code)
                         \- (触发风控) --> 3. 客情维护谈判 (Agent)
                                                                --> 4. 执行退款 API (Code)
                                                                     --> 5. 发送最终通知 (Agent)
                                                                            --> [End]
```

## 4. 节点详细设计 (Nodes)

### 4.1 节点 1：用户意图解析 (LLM Agent 节点)

- 输入：`state.user_input`
- LLM 提示词核心：

    > 你是一个数据提取助手。请分析用户的投诉文本，提取两个关键信息：
    > 1. 用户是否提及“剪了标签/洗过了/穿过了”等影响二次销售的行为，若是则 `tags_removed=True`，否则为 `False`。
    > 2. 分析用户的情绪。
    >    请以 JSON 格式返回。

- 输出：更新 `state.tags_removed` 和 `state.user_emotion`。

### 4.2 节点 2：风控与策略校验 (纯 Code 节点)

- 输入：`state.item_price`、`state.tags_removed`
- 业务逻辑（硬编码）：

```python
if state.item_price > 500 and state.tags_removed is True:
        state.policy_passed = False  # 触发风控：大额商品且影响二次销售，不允许自动全额退款
else:
        state.policy_passed = True
        state.refund_amount = state.item_price  # 允许全额退款
```

- 条件路由（Conditional Edge）：
    - 如果 `state.policy_passed == True`，路由至节点 4（执行退款 API）。
    - 如果 `state.policy_passed == False`，路由至节点 3（客情维护谈判）。

### 4.3 节点 3：客情维护谈判 (LLM Agent 节点)

- 输入：`state.user_emotion`、`state.user_input`
- Agent 设定与约束：
    - 角色：资深售后公关专家，语气必须极度温柔、充满同理心。
    - 目标：拒绝用户全额退款诉求，但提出折中方案（固定为 30% 部分退款 + 20 元优惠券）。
    - 动作：调用系统工具 `issue_coupon_tool`（发放优惠券），并将 `state.refund_amount` 设为 `item_price * 0.3`。
- 输出：生成安抚并提出方案的文本，更新 `state.refund_amount` 和 `state.coupon_issued`。

### 4.4 节点 4：执行退款 API (纯 Code 节点)

- 输入：`state.refund_amount`
- 业务逻辑：模拟调用支付网关。使用 `print()` 打印：`[SUCCESS] 已向用户原路退款 ￥XXX.XX 元`。
- 输出：确认退款成功。

### 4.5 节点 5：发送最终通知 (LLM Agent 节点)

- 输入：`state.refund_amount`、`state.coupon_issued`
- LLM 提示词核心：

    > 根据最终的退款金额 [refund_amount] 和优惠券状态 [coupon_issued]，为用户生成一封正式的结案通知邮件。要求措辞得体，明确告知钱款到账时间和优惠券使用方法。

- 输出：打印最终通知文本。

## 5. 推荐测试用例 (Test Cases)

### 5.1 测试用例 A（应直接走全额退款流程）

- 系统初始化：`item_price = 600`
- 用户输入：衣服收到了，尺码拍小了，我没试穿，吊牌都在，帮我退了吧。
- 预期路径：意图解析（`tags_removed=False`） --> 风控校验（通过） --> 执行退款（退 600 元） --> 结束。

### 5.2 测试用例 B（应触发 Agent 谈判流）

- 系统初始化：`item_price = 600`
- 用户输入：衣服质量太差了！根本不是纯棉的。我气死了，明天要穿的也耽误了！标签我已经剪掉扔了，反正不管怎么样你们必须给我退全款！
- 预期路径：意图解析（`tags_removed=True`, `emotion=angry`） --> 风控校验（拦截） --> 谈判 Agent（温柔安抚、发放 20 元券、改退款金额为 180 元） --> 执行退款（退 180 元） --> 发送最终通知 --> 结束。