#!/usr/bin/env python3
"""
评分对比脚本：对比 AI 评分 (baseline_result.csv) 与人工 Golden 评分，
计算偏差、找出 Badcase、按类型统计。

用法:
    python evals/compare_scores.py
    python evals/compare_scores.py --baseline evals/baseline_result.csv
    python evals/compare_scores.py --golden evals/eval_set_v1.csv
    python evals/compare_scores.py --output evals/comparison_report.md
    python evals/compare_scores.py --top-n 15

输出:
    - 终端: 汇总统计 + Top-N Badcase 列表
    - 可选: Markdown 报告文件
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
import traceback
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Optional

# ── UTF-8 encoding for Windows ─────────────────────────────────────
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DIMS = ["content_relevance", "structure_clarity", "evidence_support", "expression_credibility"]
DIM_LABELS = {
    "content_relevance": "内容匹配度",
    "structure_clarity": "结构清晰度",
    "evidence_support": "证据支撑度",
    "expression_credibility": "表达可信度",
}
WEIGHTS = {"content_relevance": 0.35, "structure_clarity": 0.25,
           "evidence_support": 0.25, "expression_credibility": 0.15}

# ── Badcase classification ─────────────────────────────────────────

def classify_badcase(dim: str, ai: float, golden: float) -> str:
    """Classify a large deviation into a badcase type."""
    delta = ai - golden
    abs_delta = abs(delta)

    if abs_delta < 0.8:
        return "minor_deviation"

    if delta > 0:
        # AI scored higher than human
        if delta >= 2.0:
            return "severe_over_score"
        elif delta >= 1.0:
            if dim == "evidence_support":
                return "over_score_evidence_insensitive"
            elif dim == "structure_clarity":
                return "over_score_structure_lenient"
            else:
                return "over_score_general"
        else:
            return "mild_over_score"
    else:
        # AI scored lower than human
        if abs_delta >= 2.0:
            return "severe_under_score"
        elif abs_delta >= 1.0:
            if dim == "content_relevance":
                return "under_score_content_miss"
            elif dim == "expression_credibility":
                return "under_score_credibility_harsh"
            else:
                return "under_score_general"
        else:
            return "mild_under_score"


BADCATEGORY_EXPLANATIONS = {
    "severe_over_score": "AI 严重高估 (偏差 ≥ 2.0)",
    "severe_under_score": "AI 严重低估 (偏差 ≥ 2.0)",
    "over_score_evidence_insensitive": "AI 高估证据支撑度——对数据缺失不够敏感",
    "over_score_structure_lenient": "AI 高估结构清晰度——对逻辑断裂不够敏感",
    "over_score_general": "AI 普遍偏高",
    "under_score_content_miss": "AI 低估内容匹配度——可能漏判了部分考点命中",
    "under_score_credibility_harsh": "AI 低估表达可信度——对表达真实性的判断偏严",
    "under_score_general": "AI 普遍偏低",
    "mild_over_score": "AI 轻微偏高 (0.8 ≤ dev < 1.0)",
    "mild_under_score": "AI 轻微偏低 (0.8 ≤ dev < 1.0)",
    "minor_deviation": "微小偏差 (< 0.8)",
}


# ── CLI ────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="AI vs 人工评分对比分析")
    p.add_argument("--baseline", default=str(PROJECT_ROOT / "evals" / "baseline_result.csv"),
                   help="AI 评分文件 (默认: evals/baseline_result.csv)")
    p.add_argument("--golden", default=str(PROJECT_ROOT / "evals" / "eval_set_v1.csv"),
                   help="人工 Golden 评分文件 (默认: evals/eval_set_v1.csv)")
    p.add_argument("--output", default="",
                   help="输出 Markdown 报告路径 (可选)")
    p.add_argument("--top-n", type=int, default=10,
                   help="展示偏差最大的 Top-N case (默认: 10)")
    return p.parse_args()


# ── Data Loading ───────────────────────────────────────────────────

def load_baseline(path: str) -> dict[str, dict]:
    """Load AI baseline results. Returns {eval_id: row}."""
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Baseline 文件不存在: {path}\n"
            f"  请先运行: python evals/run_eval.py"
        )
    data = {}
    with open(path, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            data[row["eval_id"]] = row
    if not data:
        raise ValueError(f"Baseline 文件为空: {path}")
    return data


def load_golden(path: str) -> dict[str, dict]:
    """Load golden scores from eval set. Returns {eval_id: row}."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Golden 评测集文件不存在: {path}")
    data = {}
    with open(path, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            data[row["eval_id"]] = row
    if not data:
        raise ValueError(f"Golden 文件为空: {path}")
    return data


# ── Analysis ───────────────────────────────────────────────────────

def compute_deviations(baseline: dict, golden: dict) -> list[dict]:
    """Compute per-case per-dimension deviations between AI and Golden."""
    results = []
    for eval_id, bl_row in baseline.items():
        if eval_id not in golden:
            print(f"⚠ {eval_id} 在 Golden 集中不存在，跳过", file=sys.stderr)
            continue

        g_row = golden[eval_id]
        case_devs = {
            "eval_id": eval_id,
            "jd_category": bl_row.get("jd_category", ""),
            "jd_level": bl_row.get("jd_level", ""),
            "dims": {},
            "total_abs_deviation": 0.0,
            "has_error": bool(bl_row.get("eval_error", "")),
        }

        for dim in DIMS:
            try:
                ai_val = float(bl_row.get(f"ai_{dim}", -1))
            except (ValueError, TypeError):
                ai_val = -1
            try:
                golden_val = float(g_row.get(f"golden_{dim}", 0))
            except (ValueError, TypeError):
                golden_val = 0

            if ai_val < 0:
                case_devs["dims"][dim] = {"ai": None, "golden": golden_val, "delta": None, "abs_delta": None, "badcase_type": "eval_error"}
                continue

            delta = round(ai_val - golden_val, 2)
            abs_delta = abs(delta)
            btype = classify_badcase(dim, ai_val, golden_val)

            case_devs["dims"][dim] = {
                "ai": ai_val,
                "golden": golden_val,
                "delta": delta,
                "abs_delta": abs_delta,
                "badcase_type": btype,
            }
            case_devs["total_abs_deviation"] += abs_delta

        # Also compare weighted totals
        try:
            ai_wt = float(bl_row.get("ai_weighted_total", -1))
        except (ValueError, TypeError):
            ai_wt = -1
        try:
            golden_wt = float(g_row.get("golden_weighted_total",
                              sum(float(g_row.get(f"golden_{d}", 0)) * WEIGHTS[d] for d in DIMS)))
        except (ValueError, TypeError):
            golden_wt = sum(float(g_row.get(f"golden_{d}", 0)) * WEIGHTS[d] for d in DIMS)

        case_devs["ai_weighted"] = ai_wt if ai_wt >= 0 else None
        case_devs["golden_weighted"] = round(golden_wt, 2)
        if ai_wt >= 0:
            case_devs["weighted_delta"] = round(ai_wt - golden_wt, 2)

        results.append(case_devs)

    if not results:
        raise ValueError("Golden 集和 Baseline 集没有共同的 eval_id。请检查两者是否来自同一批数据。")
    return results


def aggregate_stats(deviations: list[dict]) -> dict:
    """Compute aggregate statistics."""
    # Per-dimension MAE
    dim_mae = {}
    dim_me = {}  # mean error (with sign)
    for dim in DIMS:
        deltas = []
        for case in deviations:
            d = case["dims"].get(dim, {})
            if d.get("delta") is not None:
                deltas.append(d["delta"])
        dim_mae[dim] = round(sum(abs(d) for d in deltas) / len(deltas), 3) if deltas else 0
        dim_me[dim] = round(sum(deltas) / len(deltas), 3) if deltas else 0

    # Overall MAE across all dims
    all_abs = []
    for case in deviations:
        for dim in DIMS:
            d = case["dims"].get(dim, {})
            if d.get("abs_delta") is not None:
                all_abs.append(d["abs_delta"])
    overall_mae = round(sum(all_abs) / len(all_abs), 3) if all_abs else 0

    # Weighted total MAE
    wt_deltas = [abs(c["weighted_delta"]) for c in deviations if c.get("weighted_delta") is not None]
    weighted_mae = round(sum(wt_deltas) / len(wt_deltas), 3) if wt_deltas else 0

    # Badcase type distribution
    badcase_counts: dict[str, int] = defaultdict(int)
    for case in deviations:
        for dim in DIMS:
            d = case["dims"].get(dim, {})
            btype = d.get("badcase_type", "unknown")
            if btype != "minor_deviation" and btype != "eval_error":
                badcase_counts[btype] += 1

    # Per-dimension bias direction
    dim_bias = {}
    for dim in DIMS:
        me = dim_me[dim]
        if me > 0.3:
            dim_bias[dim] = "AI 系统性偏高"
        elif me < -0.3:
            dim_bias[dim] = "AI 系统性偏低"
        else:
            dim_bias[dim] = "无明显系统性偏差"

    # Success rate
    error_count = sum(1 for c in deviations if c["has_error"])
    success_count = len(deviations) - error_count

    return {
        "total_cases": len(deviations),
        "success_count": success_count,
        "error_count": error_count,
        "overall_mae": overall_mae,
        "weighted_mae": weighted_mae,
        "dim_mae": dim_mae,
        "dim_me": dim_me,
        "dim_bias": dim_bias,
        "badcase_counts": dict(badcase_counts),
    }


def top_deviations(deviations: list[dict], n: int = 10) -> list[dict]:
    """Return top-N cases sorted by total absolute deviation (descending)."""
    valid = [c for c in deviations if not c["has_error"]]
    valid.sort(key=lambda c: c["total_abs_deviation"], reverse=True)
    return valid[:n]


# ── Output ─────────────────────────────────────────────────────────

def print_summary(stats: dict, deviations: list[dict], top_n: int) -> None:
    """Print summary to terminal."""
    print(f"\n{'='*60}")
    print(f"  AI vs 人工评分 对比报告")
    print(f"{'='*60}")
    print(f"\n【数据集概况】")
    print(f"  总 case 数:     {stats['total_cases']}")
    print(f"  评测成功:       {stats['success_count']}")
    print(f"  评测失败:       {stats['error_count']}")
    print(f"  全局 MAE:       {stats['overall_mae']:.3f}")
    print(f"  加权总分 MAE:   {stats['weighted_mae']:.3f}")

    print(f"\n【分维度偏差】")
    print(f"  {'维度':<16} {'MAE':>8} {'均值误差':>10} {'偏差方向'}")
    print(f"  {'-'*50}")
    for dim in DIMS:
        label = DIM_LABELS[dim]
        mae = stats["dim_mae"][dim]
        me = stats["dim_me"][dim]
        bias = stats["dim_bias"][dim]
        sign = "+" if me > 0 else ""
        print(f"  {label:<14} {mae:>8.3f} {sign}{me:>9.3f}   {bias}")

    if stats["badcase_counts"]:
        print(f"\n【Badcase 类型分布】(偏差 ≥ 0.8)")
        for btype, count in sorted(stats["badcase_counts"].items(), key=lambda x: -x[1]):
            desc = BADCATEGORY_EXPLANATIONS.get(btype, btype)
            print(f"  {btype:<40} {count:>4}   {desc}")

    # Top-N
    top = top_deviations(deviations, top_n)
    if top:
        print(f"\n【偏差最大的 Top {len(top)} Case】")
        print(f"  {'Eval ID':<10} {'类别':<8} {'AI总分':>8} {'Golden':>8} {'偏差':>8} {'最大偏差维度'}")
        print(f"  {'-'*60}")
        for case in top:
            max_dim = max(case["dims"].items(), key=lambda x: x[1].get("abs_delta", 0))
            max_label = DIM_LABELS.get(max_dim[0], max_dim[0])
            max_abs = max_dim[1].get("abs_delta", 0)
            ai_w = case.get("ai_weighted")
            ai_str = f"{ai_w:.2f}" if ai_w is not None else "N/A"
            print(f"  {case['eval_id']:<10} {case['jd_category']:<8} {ai_str:>8} "
                  f"{case['golden_weighted']:>8} {case.get('weighted_delta', 0):>+8.2f} "
                  f"  {max_label}({max_abs:.1f})")


def generate_markdown_report(stats: dict, deviations: list[dict], top_n: int, args) -> str:
    """Generate a markdown evaluation report."""
    now = datetime.now().isoformat()
    top = top_deviations(deviations, top_n)

    lines = []
    lines.append(f"# AI 面试训练 Agent — 评测报告")
    lines.append(f"")
    lines.append(f"> 自动生成时间: {now}")
    lines.append(f"> Baseline: `{args.baseline}`")
    lines.append(f"> Golden: `{args.golden}`")
    lines.append(f"")

    # Summary
    lines.append(f"## 1. 数据集概况")
    lines.append(f"")
    lines.append(f"| 指标 | 值 |")
    lines.append(f"|------|----|")
    lines.append(f"| 总 case 数 | {stats['total_cases']} |")
    lines.append(f"| 评测成功 | {stats['success_count']} |")
    lines.append(f"| 评测失败 | {stats['error_count']} |")
    lines.append(f"| 全局 MAE（四维度） | {stats['overall_mae']:.3f} |")
    lines.append(f"| 加权总分 MAE | {stats['weighted_mae']:.3f} |")
    lines.append(f"")

    # Per-dimension
    lines.append(f"## 2. 分维度偏差分析")
    lines.append(f"")
    lines.append(f"| 维度 | MAE | 均值误差 | 偏差方向 |")
    lines.append(f"|------|-----|---------|---------|")
    for dim in DIMS:
        label = DIM_LABELS[dim]
        mae = stats["dim_mae"][dim]
        me = stats["dim_me"][dim]
        bias = stats["dim_bias"][dim]
        sign = "+" if me > 0 else ""
        lines.append(f"| {label} | {mae:.3f} | {sign}{me:.3f} | {bias} |")
    lines.append(f"")

    # Interpretation
    lines.append(f"### 偏差解读")
    lines.append(f"")
    for dim in DIMS:
        bias = stats["dim_bias"][dim]
        label = DIM_LABELS[dim]
        if "偏高" in bias:
            lines.append(f"- **{label}**: AI 评分相对人工评分偏高，可能原因：AI 对表面结构化/术语使用的奖励过度，对深层逻辑缺陷不够敏感。")
        elif "偏低" in bias:
            lines.append(f"- **{label}**: AI 评分相对人工评分偏低，可能原因：AI 对某些表达方式的判断过于严苛，或未充分理解候选人的隐含意思。")
        else:
            lines.append(f"- **{label}**: 无明显系统性偏差，AI 评分与人工评分基本一致。")
    lines.append(f"")

    # Badcase types
    if stats["badcase_counts"]:
        lines.append(f"## 3. Badcase 类型分布")
        lines.append(f"")
        lines.append(f"| Badcase 类型 | 数量 | 说明 |")
        lines.append(f"|-------------|------|------|")
        for btype, count in sorted(stats["badcase_counts"].items(), key=lambda x: -x[1]):
            desc = BADCATEGORY_EXPLANATIONS.get(btype, btype)
            lines.append(f"| {btype} | {count} | {desc} |")
        lines.append(f"")

    # Top-N
    if top:
        lines.append(f"## 4. 偏差最大的 Top {len(top)} Case")
        lines.append(f"")
        lines.append(f"| Rank | Eval ID | 类别 | AI总分 | Golden | 偏差 | 最大偏差维度 |")
        lines.append(f"|------|---------|------|--------|--------|------|-------------|")
        for rank, case in enumerate(top, 1):
            max_dim = max(case["dims"].items(), key=lambda x: x[1].get("abs_delta", 0))
            max_label = DIM_LABELS.get(max_dim[0], max_dim[0])
            max_abs = max_dim[1].get("abs_delta", 0)
            ai_w = case.get("ai_weighted")
            ai_str = f"{ai_w:.2f}" if ai_w is not None else "N/A"
            lines.append(f"| {rank} | {case['eval_id']} | {case['jd_category']} | "
                         f"{ai_str} | {case['golden_weighted']} | "
                         f"{case.get('weighted_delta', 0):+.2f} | "
                         f"{max_label} ({max_abs:.1f}) |")
        lines.append(f"")

        # Detail for each top case
        lines.append(f"### Top Case 详情")
        lines.append(f"")
        for rank, case in enumerate(top, 1):
            lines.append(f"#### {rank}. {case['eval_id']} ({case['jd_category']} · {case['jd_level']})")
            lines.append(f"")
            lines.append(f"| 维度 | AI 评分 | Golden | 偏差 | Badcase 类型 |")
            lines.append(f"|------|---------|--------|------|-------------|")
            for dim in DIMS:
                d = case["dims"].get(dim, {})
                ai = d.get("ai")
                ai_str = f"{ai:.0f}" if ai is not None else "N/A"
                delta = d.get("delta")
                delta_str = f"{delta:+.0f}" if delta is not None else "N/A"
                btype = d.get("badcase_type", "")
                lines.append(f"| {DIM_LABELS[dim]} | {ai_str} | {d.get('golden', '?')} | {delta_str} | {btype} |")
            lines.append(f"")

    # Recommendations
    lines.append(f"## 5. 改进建议")
    lines.append(f"")
    if stats["overall_mae"] > 1.0:
        lines.append(f"- ⚠ **全局 MAE 偏高 ({stats['overall_mae']:.3f})**：建议检查评估官 Prompt 的评分锚定标准是否与 Rubric 一致。")
    if stats["error_count"] > 0:
        lines.append(f"- ⚠ **{stats['error_count']} 条评测失败**：请检查 eval_error 列排查根因。")
    # Dimension-specific
    for dim in DIMS:
        if stats["dim_mae"][dim] > 1.0:
            lines.append(f"- **{DIM_LABELS[dim]} MAE > 1.0**：建议重点优化该维度的 Prompt，增加锚定案例和反例。")
    lines.append(f"- 建议每轮评测后将 Top-N Badcase 纳入回归评测集，确保修复有效。")
    lines.append(f"")

    lines.append(f"---")
    lines.append(f"*报告由 `evals/compare_scores.py` 自动生成。评测体系说明见 [`eval_readme.md`](./eval_readme.md)。*")
    lines.append(f"")

    return "\n".join(lines)


# ── Main ───────────────────────────────────────────────────────────

def main() -> None:
    args = parse_args()

    print("加载数据...")
    try:
        baseline = load_baseline(args.baseline)
        golden = load_golden(args.golden)
    except (FileNotFoundError, ValueError) as e:
        print(f"✗ 数据加载失败: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"  Baseline: {len(baseline)} 条")
    print(f"  Golden:   {len(golden)} 条")

    # Match and compute
    deviations = compute_deviations(baseline, golden)
    stats = aggregate_stats(deviations)

    # Terminal output
    print_summary(stats, deviations, args.top_n)

    # Markdown report (if --output specified)
    if args.output:
        md = generate_markdown_report(stats, deviations, args.top_n, args)
        out_dir = os.path.dirname(args.output) or "."
        os.makedirs(out_dir, exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(md)
        print(f"\n✓ Markdown 报告已保存: {args.output}")


if __name__ == "__main__":
    try:
        main()
    except FileNotFoundError as e:
        print(f"✗ 文件错误: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"✗ 数据错误: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠ 用户中断", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"✗ 未预期的错误:\n{traceback.format_exc()}", file=sys.stderr)
        sys.exit(1)
