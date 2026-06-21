# Refund Graph AI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将当前退款示例迁移为基于 LangGraph 的完整工作流，接入本地 Ollama qwen 模型，并在两条主业务路径上稳定运行。

**Architecture:** 使用 LangGraph 的 StateGraph 统一编排 5 个节点。LLM 仅负责信息提取与文案生成，策略判断、金额计算、路由和工具结果全部由 Python 代码控制，并为 LLM 失败提供轻量降级。

**Tech Stack:** Python 3.13, Poetry, LangGraph, langchain-core, langchain-ollama, pytest, Ruff, Ollama

## Global Constraints

- Python 版本保持 `>=3.13,<3.14`
- 包管理与运行方式保持 Poetry
- 本地模型通过 Ollama 默认服务访问，基础地址按 `http://localhost:11434` 处理
- 模型使用本地 qwen 标签，具体名称以本机已拉取模型为准
- 金额、规则、路由和工具执行结果不得交给 LLM 自由决定
- 当前阶段只实现 mock refund 与 mock coupon，不接真实外部系统
- 先保证两条主路径和一条降级路径可验证，再考虑 prompt 优化

---

### Task 1: Add Workflow Dependencies

**Files:**
- Modify: `/Users/wentjiang/myspace/refund_graph_AI/pyproject.toml`
- Check: `/Users/wentjiang/myspace/refund_graph_AI/README.md`

**Interfaces:**
- Consumes: 现有 Poetry 项目结构
- Produces: 可导入的 `langgraph`、`langchain_ollama.ChatOllama` 运行环境

- [ ] 在 `pyproject.toml` 中加入 `langgraph`、`langchain-core`、`langchain-ollama` 依赖。
- [ ] 保持现有 `pytest`、`ruff`、`project.scripts` 配置不变。
- [ ] 确认 README 中现有 Poetry 启动方式无需重写，只在必要时补一行 Ollama 前置说明。
- [ ] 安装依赖并验证可以成功导入 `StateGraph` 和 `ChatOllama`。

### Task 2: Reshape the Shared State

**Files:**
- Modify: `/Users/wentjiang/myspace/refund_graph_AI/src/refund_graph_ai/state.py`
- Test: `/Users/wentjiang/myspace/refund_graph_AI/tests/test_workflow.py`

**Interfaces:**
- Consumes: 当前 `RefundState` 字段 `user_input`、`item_price`、`tags_removed`、`user_emotion`、`policy_passed`、`refund_amount`、`coupon_issued`、`negotiation_log`
- Produces: LangGraph 可用状态结构，包含新增字段 `final_notification`、`refund_result`、`error_msg`

- [ ] 明确状态结构采用 LangGraph 友好的字典式定义或 TypedDict 方案。
- [ ] 保留现有业务字段默认语义，避免改变需求文档中的含义。
- [ ] 新增 `final_notification` 用于保存节点 5 输出。
- [ ] 新增 `refund_result` 用于保存节点 4 执行结果。
- [ ] 新增 `error_msg` 用于节点降级和失败诊断。

### Task 3: Rebuild the Workflow as a StateGraph

**Files:**
- Modify: `/Users/wentjiang/myspace/refund_graph_AI/src/refund_graph_ai/workflow.py`
- Modify: `/Users/wentjiang/myspace/refund_graph_AI/src/refund_graph_ai/main.py`

**Interfaces:**
- Consumes: Task 2 的状态结构
- Produces: `run_workflow(user_input: str, item_price: float = 600.0) -> tuple[state, list[str]]` 或等价稳定接口

- [ ] 在 `workflow.py` 中创建 `StateGraph` 主干。
- [ ] 添加节点 `parse_user_intent`、`risk_policy_check`、`negotiate_customer_care`、`execute_refund`、`generate_final_notification`。
- [ ] 添加从 `risk_policy_check` 出发的条件路由，基于 `policy_passed` 决定下一节点。
- [ ] 让两条路径最终都进入 `generate_final_notification`，保持统一收尾。
- [ ] 更新 `main.py`，使演示入口打印关键状态和生成文本，而不是依赖旧的手动流程。

### Task 4: Implement Intent Parsing with Structured LLM Output

**Files:**
- Modify: `/Users/wentjiang/myspace/refund_graph_AI/src/refund_graph_ai/workflow.py`
- Test: `/Users/wentjiang/myspace/refund_graph_AI/tests/test_workflow.py`

**Interfaces:**
- Consumes: `user_input: str`
- Produces: `tags_removed: bool` 与 `user_emotion: str`

- [ ] 初始化 `ChatOllama`，模型名使用本地 qwen 标签。
- [ ] 为 `parse_user_intent` 设计固定输出 schema，只提取 `tags_removed` 和 `user_emotion`。
- [ ] 将 JSON 解析或结构化输出校验限制在该节点内，不让后续节点关心 LLM 文本格式。
- [ ] 当结构化输出失败时，使用关键词规则兜底 `tags_removed`。
- [ ] 当情绪识别失败时，将 `user_emotion` 设为 `unknown` 或简化规则值。

### Task 5: Implement Negotiation as LLM Copy + Code-Controlled Compensation

**Files:**
- Modify: `/Users/wentjiang/myspace/refund_graph_AI/src/refund_graph_ai/workflow.py`
- Test: `/Users/wentjiang/myspace/refund_graph_AI/tests/test_workflow.py`

**Interfaces:**
- Consumes: `user_input`、`user_emotion`、`item_price`
- Produces: `refund_amount`、`coupon_issued`、`negotiation_log`

- [ ] 在 `workflow.py` 中定义本地 `issue_coupon_tool` mock 或薄封装函数。
- [ ] 将 `refund_amount` 固定设置为 `item_price * 0.3`。
- [ ] 将 `coupon_issued` 固定设置为成功发券后的结果。
- [ ] 使用 LLM 只生成安抚与协商文案，并写入 `negotiation_log`。
- [ ] 若 LLM 调用失败，写入固定模板文案，不影响赔付逻辑和后续退款执行。

### Task 6: Implement Refund Execution and Final Notification

**Files:**
- Modify: `/Users/wentjiang/myspace/refund_graph_AI/src/refund_graph_ai/workflow.py`
- Modify: `/Users/wentjiang/myspace/refund_graph_AI/src/refund_graph_ai/main.py`

**Interfaces:**
- Consumes: `refund_amount`、`coupon_issued`
- Produces: `refund_result`、`final_notification`

- [ ] 在 `execute_refund` 中保留 mock 支付逻辑，但将结果写入 `refund_result`。
- [ ] 保持成功消息与需求文档一致，即包含退款金额。
- [ ] 在 `generate_final_notification` 中根据 `refund_amount` 和 `coupon_issued` 生成正式通知文本。
- [ ] 若通知节点失败，回退到固定模板，确保流程总能结束并给出可展示结果。

### Task 7: Add Focused Verification Coverage

**Files:**
- Modify: `/Users/wentjiang/myspace/refund_graph_AI/tests/test_workflow.py`
- Check: `/Users/wentjiang/myspace/refund_graph_AI/README.md`

**Interfaces:**
- Consumes: `run_workflow(...)`
- Produces: 覆盖两条主路径和一条降级路径的最小测试集

- [ ] 保留“全额退款路径”测试，断言 `policy_passed=True`、`refund_amount=600.0`、`coupon_issued=False`。
- [ ] 保留“协商退款路径”测试，断言 `policy_passed=False`、`refund_amount=180.0`、`coupon_issued=True`。
- [ ] 补一条 LLM 解析失败或非法输出测试，断言流程仍可继续，并写入可观测错误信息或采用兜底值。
- [ ] 运行 `pytest` 验证测试通过。
- [ ] 如 README 与真实运行前提不一致，补足最小运行说明。

### Task 8: Manual End-to-End Validation

**Files:**
- Check: `/Users/wentjiang/myspace/refund_graph_AI/src/refund_graph_ai/main.py`
- Check: `/Users/wentjiang/myspace/refund_graph_AI/docs/requirement.md`

**Interfaces:**
- Consumes: 完整工作流实现
- Produces: 可演示的 CLI 输出和对需求文档的对照确认

- [ ] 使用测试用例 A 文本手工运行，确认路径为解析 -> 风控通过 -> 退款 -> 通知。
- [ ] 使用测试用例 B 文本手工运行，确认路径为解析 -> 风控拦截 -> 谈判 -> 退款 -> 通知。
- [ ] 检查打印输出与状态值是否与需求文档一致。
- [ ] 检查 `error_msg` 在正常路径为空，在降级路径可用于诊断。

## Verification Summary

1. `poetry install`
2. `poetry run pytest`
3. `poetry run refund-graph-ai`
4. 在 Ollama 运行时分别手工输入两条示例文本，核对结果

## Scope Boundaries

- Included: LangGraph 编排、本地 Ollama 接入、3 个 LLM 节点、2 个代码节点、mock 工具、基础测试、轻量降级。
- Excluded: 真实支付网关、真实优惠券系统、多轮谈判状态机、后台管理界面、复杂可观测性平台。

## Self-Review Notes

- 需求中的 5 个节点均已映射到独立任务。
- 风控分支、谈判赔付比例、优惠券金额、最终通知均已覆盖。
- 当前计划未展开真实外部系统集成，符合既定范围边界。
