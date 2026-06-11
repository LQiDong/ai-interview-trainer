# AI 面试训练 Agent — 评测报告

> 自动生成时间: 2026-06-11T18:45:55.821038
> Baseline: `D:\DESK\AI产品经理\面试项目\evals\baseline_result.csv`
> Golden: `D:\DESK\AI产品经理\面试项目\evals\eval_set_v1.csv`

## 1. 数据集概况

| 指标 | 值 |
|------|----|
| 总 case 数 | 10 |
| 评测成功 | 10 |
| 评测失败 | 0 |
| 全局 MAE（四维度） | 0.700 |
| 加权总分 MAE | 0.380 |

## 2. 分维度偏差分析

| 维度 | MAE | 均值误差 | 偏差方向 |
|------|-----|---------|---------|
| 内容匹配度 | 0.700 | -0.700 | AI 系统性偏低 |
| 结构清晰度 | 0.800 | -0.600 | AI 系统性偏低 |
| 证据支撑度 | 0.900 | +0.300 | 无明显系统性偏差 |
| 表达可信度 | 0.400 | 0.000 | 无明显系统性偏差 |

### 偏差解读

- **内容匹配度**: AI 评分相对人工评分偏低，可能原因：AI 对某些表达方式的判断过于严苛，或未充分理解候选人的隐含意思。
- **结构清晰度**: AI 评分相对人工评分偏低，可能原因：AI 对某些表达方式的判断过于严苛，或未充分理解候选人的隐含意思。
- **证据支撑度**: 无明显系统性偏差，AI 评分与人工评分基本一致。
- **表达可信度**: 无明显系统性偏差，AI 评分与人工评分基本一致。

## 3. Badcase 类型分布

| Badcase 类型 | 数量 | 说明 |
|-------------|------|------|
| under_score_general | 8 | AI 普遍偏低 |
| under_score_content_miss | 7 | AI 低估内容匹配度——可能漏判了部分考点命中 |
| over_score_evidence_insensitive | 4 | AI 高估证据支撑度——对数据缺失不够敏感 |
| over_score_general | 2 | AI 普遍偏高 |
| under_score_credibility_harsh | 2 | AI 低估表达可信度——对表达真实性的判断偏严 |
| severe_under_score | 1 | AI 严重低估 (偏差 ≥ 2.0) |
| severe_over_score | 1 | AI 严重高估 (偏差 ≥ 2.0) |
| over_score_structure_lenient | 1 | AI 高估结构清晰度——对逻辑断裂不够敏感 |

## 4. 偏差最大的 Top 10 Case

| Rank | Eval ID | 类别 | AI总分 | Golden | 偏差 | 最大偏差维度 |
|------|---------|------|--------|--------|------|-------------|
| 1 | E010 | Agent产品经理 | 1.05 | 1.75 | -0.70 | 内容匹配度 (1.0) |
| 2 | E001 | AI产品经理 | 0.90 | 1.75 | -0.85 | 内容匹配度 (1.0) |
| 3 | E002 | AI产品经理 | 1.75 | 2.0 | -0.25 | 结构清晰度 (2.0) |
| 4 | E005 | AI产品经理 | 1.75 | 2.5 | -0.75 | 内容匹配度 (1.0) |
| 5 | E006 | AI产品经理 | 1.40 | 1.25 | +0.15 | 证据支撑度 (2.0) |
| 6 | E008 | AI产品运营 | 1.00 | 1.15 | -0.15 | 结构清晰度 (1.0) |
| 7 | E009 | AI产品经理 | 1.90 | 1.75 | +0.15 | 内容匹配度 (1.0) |
| 8 | E003 | Agent产品经理 | 0.75 | 0.75 | +0.00 | 结构清晰度 (1.0) |
| 9 | E004 | AI产品运营 | 1.65 | 1.85 | -0.20 | 内容匹配度 (1.0) |
| 10 | E007 | Agent产品经理 | 1.65 | 2.25 | -0.60 | 内容匹配度 (1.0) |

### Top Case 详情

#### 1. E010 (Agent产品经理 · 中级)

| 维度 | AI 评分 | Golden | 偏差 | Badcase 类型 |
|------|---------|--------|------|-------------|
| 内容匹配度 | 1 | 2.0 | -1 | under_score_content_miss |
| 结构清晰度 | 1 | 2.0 | -1 | under_score_general |
| 证据支撑度 | 0 | 1.0 | -1 | under_score_general |
| 表达可信度 | 3 | 2.0 | +1 | over_score_general |

#### 2. E001 (AI产品经理 · 高级)

| 维度 | AI 评分 | Golden | 偏差 | Badcase 类型 |
|------|---------|--------|------|-------------|
| 内容匹配度 | 1 | 2.0 | -1 | under_score_content_miss |
| 结构清晰度 | 1 | 2.0 | -1 | under_score_general |
| 证据支撑度 | 0 | 1.0 | -1 | under_score_general |
| 表达可信度 | 2 | 2.0 | +0 | minor_deviation |

#### 3. E002 (AI产品经理 · 高级)

| 维度 | AI 评分 | Golden | 偏差 | Badcase 类型 |
|------|---------|--------|------|-------------|
| 内容匹配度 | 2 | 2.0 | +0 | minor_deviation |
| 结构清晰度 | 0 | 2.0 | -2 | severe_under_score |
| 证据支撑度 | 3 | 2.0 | +1 | over_score_evidence_insensitive |
| 表达可信度 | 2 | 2.0 | +0 | minor_deviation |

#### 4. E005 (AI产品经理 · 专家)

| 维度 | AI 评分 | Golden | 偏差 | Badcase 类型 |
|------|---------|--------|------|-------------|
| 内容匹配度 | 2 | 3.0 | -1 | under_score_content_miss |
| 结构清晰度 | 2 | 2.0 | +0 | minor_deviation |
| 证据支撑度 | 1 | 2.0 | -1 | under_score_general |
| 表达可信度 | 2 | 3.0 | -1 | under_score_credibility_harsh |

#### 5. E006 (AI产品经理 · 中级)

| 维度 | AI 评分 | Golden | 偏差 | Badcase 类型 |
|------|---------|--------|------|-------------|
| 内容匹配度 | 1 | 2.0 | -1 | under_score_content_miss |
| 结构清晰度 | 1 | 1.0 | +0 | minor_deviation |
| 证据支撑度 | 2 | 0.0 | +2 | severe_over_score |
| 表达可信度 | 2 | 2.0 | +0 | minor_deviation |

#### 6. E008 (AI产品运营 · 初级)

| 维度 | AI 评分 | Golden | 偏差 | Badcase 类型 |
|------|---------|--------|------|-------------|
| 内容匹配度 | 1 | 1.0 | +0 | minor_deviation |
| 结构清晰度 | 1 | 2.0 | -1 | under_score_general |
| 证据支撑度 | 1 | 0.0 | +1 | over_score_evidence_insensitive |
| 表达可信度 | 1 | 2.0 | -1 | under_score_credibility_harsh |

#### 7. E009 (AI产品经理 · 高级)

| 维度 | AI 评分 | Golden | 偏差 | Badcase 类型 |
|------|---------|--------|------|-------------|
| 内容匹配度 | 1 | 2.0 | -1 | under_score_content_miss |
| 结构清晰度 | 3 | 2.0 | +1 | over_score_structure_lenient |
| 证据支撑度 | 2 | 1.0 | +1 | over_score_evidence_insensitive |
| 表达可信度 | 2 | 2.0 | +0 | minor_deviation |

#### 8. E003 (Agent产品经理 · 中级)

| 维度 | AI 评分 | Golden | 偏差 | Badcase 类型 |
|------|---------|--------|------|-------------|
| 内容匹配度 | 1 | 1.0 | +0 | minor_deviation |
| 结构清晰度 | 0 | 1.0 | -1 | under_score_general |
| 证据支撑度 | 1 | 0.0 | +1 | over_score_evidence_insensitive |
| 表达可信度 | 1 | 1.0 | +0 | minor_deviation |

#### 9. E004 (AI产品运营 · 中级)

| 维度 | AI 评分 | Golden | 偏差 | Badcase 类型 |
|------|---------|--------|------|-------------|
| 内容匹配度 | 1 | 2.0 | -1 | under_score_content_miss |
| 结构清晰度 | 3 | 3.0 | +0 | minor_deviation |
| 证据支撑度 | 1 | 1.0 | +0 | minor_deviation |
| 表达可信度 | 2 | 1.0 | +1 | over_score_general |

#### 10. E007 (Agent产品经理 · 高级)

| 维度 | AI 评分 | Golden | 偏差 | Badcase 类型 |
|------|---------|--------|------|-------------|
| 内容匹配度 | 1 | 2.0 | -1 | under_score_content_miss |
| 结构清晰度 | 2 | 3.0 | -1 | under_score_general |
| 证据支撑度 | 2 | 2.0 | +0 | minor_deviation |
| 表达可信度 | 2 | 2.0 | +0 | minor_deviation |

## 5. 改进建议

- 建议每轮评测后将 Top-N Badcase 纳入回归评测集，确保修复有效。

---
*报告由 `evals/compare_scores.py` 自动生成。评测体系说明见 [`eval_readme.md`](./eval_readme.md)。*
