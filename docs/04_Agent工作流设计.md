# Agent 工作流设计

> **文档状态**：V1.0 | **创建日期**：2026-06-11 | **依赖**：[PRD](./01_PRD_AI面试训练Agent.md)

---

## 1. 架构总览

### 1.1 管线拓扑

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ JD       │    │ 出题官    │    │ 面试官    │    │ 评估官    │    │ 教练      │    │ Judge    │
│ Parser   │───▶│ Agent    │───▶│ Agent    │───▶│ Agent    │───▶│ Agent    │───▶│ Agent    │
│ Agent    │    │          │    │ (多轮)   │    │          │    │          │    │          │
└──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘
     │               │               │               │               │               │
     ▼               ▼               ▼               ▼               ▼               ▼
 岗位画像        面试题+追问树    完整对话记录     四维评分结果    教练改进建议     复核报告
 (JSON)          (JSON)          (Array)          (JSON)          (JSON)          (JSON)
                                                      │               │
                                                      ▼               ▼
                                                  ┌──────────────────────┐
                                                  │   报告生成器          │
                                                  │   (非Agent，模板引擎) │
                                                  └──────────────────────┘
                                                             │
                                                             ▼
                                                      诊断报告 (Markdown)
```

### 1.2 为何采用管线而非端到端

| 方案 | 优点 | 缺点 | 结论 |
|------|------|------|------|
| 端到端单模型 | 简单，延迟低 | 评估不可解释、追问质量不可控、无法独立优化各环节 | ❌ |
| Agent 管线（本方案） | 每环节可独立评测和迭代、输出可解释、错误可追溯 | 延迟高、上下文传递有损耗 | ✅ MVP 采用 |
| 全自动 Multi-Agent 辩论 | 理论上质量最高 | 延迟极高、成本高、调试困难 | 🔮 V2 探索 |

---

## 2. 详细工作流

### 2.1 Phase 0：会话初始化

**触发**：用户粘贴 JD 并点击"开始面试"

**步骤**：
1. 前端收集 `{{jd_text}}` 和 `{{target_position}}`（可选）
2. Orchestrator 创建会话上下文 `SessionContext`：
   ```json
   {
     "session_id": "uuid",
     "jd_text": "...",
     "target_position": null,
     "pressure_level": "moderate",
     "max_rounds": 25,
     "max_follow_ups": 4,
     "created_at": "ISO timestamp"
   }
   ```
3. 进入 Phase 1

### 2.2 Phase 1：JD 解析

```
Orchestrator
    │
    ├── 调用 JD Parser Agent
    │   输入: {{jd_text}}, {{target_position}}
    │   输出: JobProfile (JSON)
    │
    ├── 校验输出 JSON 合法性
    │   ├── JSON.parse 成功 → 继续
    │   └── JSON.parse 失败 → 重试 1 次 → 仍失败则降级为模板化解析
    │
    └── 将 JobProfile 写入 SessionContext
         ↓
      进入 Phase 2
```

**Agent 文件**：[`prompts/jd_parser_agent.md`](../prompts/jd_parser_agent.md)

**输出产物**：`JobProfile` — 结构化岗位画像

**异常处理**：
- JSON 解析失败 → 重试 1 次（附加 "请仅输出 JSON" 的系统提示）
- 仍失败 → 降级：使用正则提取关键字段（岗位名称、技能关键词），标记 `confidence: "low"`
- 置信度 `"low"` 时 → 前端提示用户"JD 信息不够完整，是否补充更多细节？"

### 2.3 Phase 2：出题

```
Orchestrator
    │
    ├── 调用出题官 Agent（本项目未单独提供 prompt 文件，逻辑内置于面试官 Agent 的 question_set 中）
    │   输入: JobProfile, interview_focus_areas
    │   输出: QuestionSet (JSON) — 包含 5-8 道题，每题含追问树
    │
    ├── 校验题目数量在 5-8 范围内
    │
    └── 将 QuestionSet 写入 SessionContext
         ↓
      进入 Phase 3
```

> **说明**：出题官 Agent 的完整 prompt 将在后续迭代中独立抽取为 `prompts/question_designer_agent.md`。当前 MVP 版本的出题逻辑在面试官 Agent 的 `question_set` 生成中体现。

**输出产物**：`QuestionSet` — 面试题列表 + 追问树

**题量规则**：
- 最少 5 题，最多 8 题
- 每道题至少覆盖 1 个 `interview_focus_areas` 中的考察方向
- 题型分布：行为面试题 40%、案例分析题 30%、专业知识题 20%、情境模拟题 10%

### 2.4 Phase 3：多轮面试对话

这是整个工作流中**唯一与用户实时交互的阶段**。

```
Orchestrator
    │
    ├── 初始化: current_question_index = 0, round = 0
    │
    └── 对话循环:
         │
         ├── [Orchestrator] 获取当前题目 + 追问深度
         │
         ├── [Orchestrator] 调用面试官 Agent
         │   输入: 当前题目, 追问深度, 历史对话, 追问决策逻辑
         │   输出: InterviewerAction (JSON)
         │
         ├── [Orchestrator] 解析 action:
         │   ├── action == "ask_question" → 展示题目给用户 → 等待用户输入
         │   ├── action == "follow_up"   → 展示追问给用户 → 等待用户输入
         │   └── action == "end_interview" → 退出循环，进入 Phase 4
         │
         ├── [用户输入后] 将本轮对话追加到 interview_transcript[]
         │
         ├── [Orchestrator] 检查终止条件:
         │   ├── round >= max_rounds (25) → 强制结束
         │   ├── current_question_index >= len(questions) AND 当前无活跃追问 → 自然结束
         │   └── 用户主动发送 "/end" → 用户主动结束
         │
         └── round += 1, 继续循环
              ↓
           进入 Phase 4
```

**Agent 文件**：[`prompts/interviewer_agent.md`](../prompts/interviewer_agent.md)

**上下文管理策略**：
- 面试官 Agent 每轮接收的是**压缩后的历史对话**（最近 10 轮完整保留 + 更早轮次做摘要压缩）
- 压缩方式：对 10 轮之前的对话，每道题只保留"题目 + 用户核心观点摘要 + 追问深度"，去掉冗余的措辞细节
- 压缩阈值：当 `interview_transcript` 超过 15 轮时触发第一次压缩

**对话数据结构**：
```json
{
  "round": 1,
  "question_id": 1,
  "follow_up_depth": 0,
  "interviewer_message": "请做一下自我介绍，重点说说你在AI产品方向的经验。",
  "candidate_message": "我目前在一家SaaS公司做产品经理...",
  "timestamp": "ISO"
}
```

### 2.5 Phase 4：四维评估

```
Orchestrator
    │
    ├── 对 interview_transcript 做上下文压缩（保留全部对话但做文本精简）
    │
    ├── 调用评估官 Agent
    │   输入: JobProfile, QuestionSet, interview_transcript (压缩版)
    │   输出: EvaluationResult (JSON)
    │
    ├── 校验:
    │   ├── per_question_scores 数量 === 实际回答的题目数
    │   ├── 每道题都有 4 个维度的评分
    │   ├── 每个分数在 0-3 范围内且为整数
    │   ├── score ≤ 1 的维度 deduction_points 非空
    │   └── weighted_total_score 计算公式正确
    │
    ├── 校验失败 → 重试 1 次（附校验错误信息）
    │
    └── 将 EvaluationResult 写入 SessionContext
         ↓
      进入 Phase 5
```

**Agent 文件**：[`prompts/evaluator_agent.md`](../prompts/evaluator_agent.md)

**评分体系提醒**：

| 维度 | 分值 | 权重 |
|------|------|------|
| 内容匹配度 | 0-3 | 35% |
| 结构清晰度 | 0-3 | 25% |
| 证据支撑度 | 0-3 | 25% |
| 表达可信度 | 0-3 | 15% |

**压缩策略**（Phase 4 专用）：
- 评估官需要看到完整对话，但 token 成本需要控制
- 对每轮对话做**文本精简**而非截断：保留语义完整的前提下，去掉口语化冗余（如"嗯""那个""就是说"等填充词），将长句缩为要点
- 被精简的原文保留在 `interview_transcript` 原始版本中，仅传递给评估官时使用精简版

### 2.6 Phase 5：教练建议

```
Orchestrator
    │
    ├── 调用教练 Agent
    │   输入: EvaluationResult, interview_transcript (精简版), JobProfile
    │   输出: CoachingResult (JSON)
    │
    ├── 校验:
    │   ├── per_question_coaching 覆盖了所有评估官指出 deduction_points 的题目
    │   ├── top_3_actions 按优先级排序
    │   ├── 每条 coaching_entry 的 target_dimension 和 deduction_point_from_evaluator 明确
    │   └── 无过度承诺表述（正则预检 + LLM 检查并行）
    │
    └── 将 CoachingResult 写入 SessionContext
         ↓
      进入 Phase 6
```

**Agent 文件**：[`prompts/coach_agent.md`](../prompts/coach_agent.md)

**教练-评估关联校验**：
- Orchestrator 提取 EvaluationResult 中所有 `deduction_points` 的 `(question_id, dimension)` 键
- 逐一检查 CoachingResult 中是否有对应的 `coaching_entry`
- 缺失项 > 0 → 记录为 `coverage_gap`，传递给 Judge 复核

### 2.7 Phase 6：Judge 复核

```
Orchestrator
    │
    ├── 调用 Judge Agent
    │   输入: EvaluationResult, CoachingResult, interview_transcript (精简版)
    │   输出: JudgeResult (JSON)
    │
    ├── 解析 overall_verdict:
    │   ├── "pass" → 直接生成报告
    │   ├── "pass_with_issues" → 生成报告，Judge 的 issues 附在报告"复核意见"区
    │   └── "fail" → 阻断报告生成，返回系统错误 + Judge issues 供调试
    │
    └── 进入 Phase 7
```

**Agent 文件**：[`prompts/judge_agent.md`](../prompts/judge_agent.md)

**Judge 的四种检查项**：

| 检查项 | 检查目标 | 不通过时的处理 |
|--------|---------|--------------|
| 分数-评语一致性 | 评分与 evidence 是否自洽 | `pass_with_issues` → 报告标注 |
| 低分扣分点完整性 | score ≤ 1 时 deduction_points 是否具体 | `pass_with_issues` → 报告标注 |
| 教练-评估对齐 | 教练建议是否回应了评估扣分点 | 严重缺失时 → `fail` |
| 过度承诺检测 | 教练是否出现虚假保证 | 发现即 → `pass_with_issues`，但必须标注 |

### 2.8 Phase 7：诊断报告生成

```
Orchestrator
    │
    ├── 聚合所有产物:
    │   ├── JobProfile
    │   ├── EvaluationResult
    │   ├── CoachingResult
    │   ├── JudgeResult
    │   └── interview_transcript
    │
    ├── 报告生成器（模板引擎，非 LLM 调用）
    │   输入: 以上所有 JSON
    │   输出: Markdown 格式诊断报告
    │
    ├── 注入强制声明:
    │   ├── "本报告由AI生成，不构成面试通过保证"
    │   └── "不替代真实面试官的专业判断"
    │
    └── 返回前端渲染
```

---

## 3. Orchestrator 核心职责

Orchestrator 不参与内容生成，其职责边界如下：

### 3.1 路由

```
User Input → Orchestrator 判断当前 Phase → 路由到对应 Agent → 收集输出 → 进入下一 Phase
```

### 3.2 上下文管理

| 策略 | 适用阶段 | 说明 |
|------|---------|------|
| 原始传递 | Phase 1 (JD Parser) | JD 文本较短，无需压缩 |
| 完整传递 | Phase 2 (出题) | 题目生成需要完整的岗位画像 |
| 滑动窗口 + 摘要 | Phase 3 (面试官) | 最近 10 轮完整，更早轮次摘要 |
| 文本精简 | Phase 4-6 (评估/教练/Judge) | 去除口语冗余，保留语义完整 |

### 3.3 异常处理

```
Agent 调用
    │
    ├── 成功（JSON 合法 + 校验通过）→ 继续
    │
    ├── JSON 解析失败 → 重试 1 次（增强 System Prompt: "仅输出JSON"）
    │   ├── 重试成功 → 继续
    │   └── 重试失败 → 降级策略
    │
    ├── JSON 合法但校验不通过 → 重试 1 次（附校验错误详情）
    │   ├── 重试成功 → 继续
    │   └── 重试失败 → 标记 confidence: low，继续流程（不阻断）
    │
    └── LLM API 超时/限流 → 指数退避重试 2 次
        ├── 成功 → 继续
        └── 仍失败 → 返回用户友好错误信息
```

### 3.4 降级策略

| 场景 | 降级方案 |
|------|---------|
| JD Parser 反复失败 | 使用正则提取基本字段，引导用户手动补充 |
| 评估官反复失败 | 降级为简化版评估（仅总分 + 一句评语），报告标注"简版评估" |
| 教练/Judge 失败 | 跳过该阶段，报告标注"本报告不含教练建议/Judge复核" |

---

## 4. 数据流 & 状态管理

### 4.1 SessionContext 生命周期

```
创建 (Phase 0) → 写入 (各 Phase 产出) → 读取 (后续 Phase 消费) → 销毁 (报告生成后)
```

SessionContext 在 MVP 阶段存于服务端内存（或浏览器 localStorage），报告展示给用户后即销毁，**不做持久化存储**。

### 4.2 各阶段输入输出矩阵

| Phase | Agent | 输入来源 | 输出产物 | 下游消费者 |
|-------|-------|---------|---------|-----------|
| 1 | JD Parser | 用户输入 | `JobProfile` | Phase 2, 4, 5 |
| 2 | 出题官 | Phase 1 输出 | `QuestionSet` | Phase 3, 4 |
| 3 | 面试官 | Phase 2 输出 + 用户实时输入 | `InterviewTranscript` | Phase 4, 5, 6 |
| 4 | 评估官 | Phase 1, 2, 3 输出 | `EvaluationResult` | Phase 5, 6, 7 |
| 5 | 教练 | Phase 1, 3, 4 输出 | `CoachingResult` | Phase 6, 7 |
| 6 | Judge | Phase 3, 4, 5 输出 | `JudgeResult` | Phase 7 |
| 7 | 报告生成器 | Phase 1-6 全部输出 | `DiagnosisReport` | 用户 |

---

## 5. 并发 & 延迟优化（V1.1 规划）

当前 MVP 管线是**完全串行**的。未来 V1.1 可优化的并行点：

```
Phase 4 (评估官) ─────────────────┐
                                  ├──▶ Phase 6 (Judge) ──▶ Phase 7 (报告)
Phase 5 (教练) ──────────────────┘
```

即评估官和教练可以**并行执行**（教练需要评估结果中的 `deduction_points`，但不需要 Coach 输出完成后才能开始——等等，教练依赖评估结果，所以不能并行）。

**实际可并行的点**：Judge 的四项检查可以并行执行（4 个独立检查，互不依赖），降低 Phase 6 延迟。

---

## 6. 关键设计决策记录

| 决策 | 选项 A | 选项 B | 选择 | 理由 |
|------|--------|--------|------|------|
| Judge 能否修改评分？ | 能 | 不能 | **B** | Judge 是审核方而非评估方。若允许修改评分，会模糊职责边界且难以调试是哪一环节出了问题 |
| 评估维度数量 | 3 维 | 4 维 | **B（4维）** | 内容匹配度+结构清晰度+证据支撑度+表达可信度的四维划分，既能覆盖面试评估的关键面，又不会因维度过多导致评分噪音 |
| 教练是否需要 interview_transcript？ | 需要 | 不需要 | **A（需要）** | 教练的范例回答需要参考原始对话中的具体语境，仅靠评估官的 evidence 摘要可能丢失关键语境 |
| 对话上下文压缩策略 | 截断 | 精简 | **B（精简）** | 截断可能丢失关键信息，精简保留语义完整的同时控制 token 成本 |
| MVP 是否做流式对话 | 做 | 不做 | **B（不做）** | 流式对话增加工程复杂度，MVP 先验证 Agent 管线质量，体验优化放 V1.1 |

---

## 附录 A：Prompt 文件索引

| Agent | Prompt 文件 | 核心输入 | 核心输出 |
|-------|-----------|---------|---------|
| JD Parser | [`prompts/jd_parser_agent.md`](../prompts/jd_parser_agent.md) | JD 原文 | 岗位画像 JSON |
| 面试官 | [`prompts/interviewer_agent.md`](../prompts/interviewer_agent.md) | 岗位画像 + 题库 | 面试官动作 JSON |
| 评估官 | [`prompts/evaluator_agent.md`](../prompts/evaluator_agent.md) | 对话记录 + 岗位画像 | 四维评分 JSON |
| 教练 | [`prompts/coach_agent.md`](../prompts/coach_agent.md) | 评估结果 + 对话记录 | 改进建议 JSON |
| Judge | [`prompts/judge_agent.md`](../prompts/judge_agent.md) | 评估结果 + 教练结果 + 对话记录 | 复核报告 JSON |

---

## 附录 B：版本记录

| 版本 | 日期 | 变更内容 |
|------|------|---------|
| V1.0 | 2026-06-11 | 初始版本，定义 7 Phase 管线 + 5 个 Agent Prompt + Orchestrator 职责 |
