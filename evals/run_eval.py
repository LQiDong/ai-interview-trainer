#!/usr/bin/env python3
"""
自动化评测脚本：读取 eval_set_v1.csv，逐条调用评估官 Agent，输出 AI 评分。

用法:
    python evals/run_eval.py                          # mock 模式（默认）
    python evals/run_eval.py --real                   # 真实 LLM 模式
    python evals/run_eval.py --input evals/eval_set_v1.csv
    python evals/run_eval.py --output evals/baseline_result.csv
    python evals/run_eval.py --retries 3              # 失败重试次数

要求:
    - 没有 API Key 时自动降级为 mock 模式
    - 逐条失败不阻断整体流程
    - 所有错误清晰输出到 stderr
    - mock 模式结果可复现（基于输入 hash 的确定性评分）
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sys
import time
import traceback
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

# ── Path setup ─────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

DIMS = ["content_relevance", "structure_clarity", "evidence_support", "expression_credibility"]
DIM_LABELS = {
    "content_relevance": "内容匹配度",
    "structure_clarity": "结构清晰度",
    "evidence_support": "证据支撑度",
    "expression_credibility": "表达可信度",
}


# ── CLI ────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="AI 面试训练 Agent — 自动化评测脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python evals/run_eval.py                           # mock 模式
  python evals/run_eval.py --real                    # 真实 LLM
  python evals/run_eval.py --input my_evals.csv --output my_baseline.csv
        """,
    )
    p.add_argument("--input", default=str(PROJECT_ROOT / "evals" / "eval_set_v1.csv"),
                   help="评测集 CSV 路径 (默认: evals/eval_set_v1.csv)")
    p.add_argument("--output", default=str(PROJECT_ROOT / "evals" / "baseline_result.csv"),
                   help="AI 评分输出路径 (默认: evals/baseline_result.csv)")
    p.add_argument("--real", action="store_true",
                   help="使用真实 LLM 模式（需设置 API_KEY 环境变量）")
    p.add_argument("--model", default="",
                   help="覆盖 MODEL_NAME 环境变量")
    p.add_argument("--retries", type=int, default=2,
                   help="单条失败重试次数 (默认: 2)")
    p.add_argument("--verbose", "-v", action="store_true",
                   help="显示详细评测过程")
    return p.parse_args()


# ── Deterministic Mock Scoring ─────────────────────────────────────

def _hash_to_score(text: str, dim: str, seed: int = 42) -> int:
    """
    Deterministic mock score (0-3) based on input hash.
    Same input → same score every time. Different inputs → varied scores.
    """
    # Combine text + dimension + seed for per-dimension variation
    payload = f"{text}|{dim}|{seed}"
    h = hashlib.sha256(payload.encode()).digest()
    # Use first 2 bytes to get a value 0-65535
    val = int.from_bytes(h[:2], "big")
    # Map to 0-3 distribution: 0(10%), 1(35%), 2(40%), 3(15%)
    normalized = val / 65536.0
    if normalized < 0.10:
        return 0
    elif normalized < 0.45:
        return 1
    elif normalized < 0.85:
        return 2
    else:
        return 3


def _generate_mock_evaluation(row: dict) -> dict:
    """
    Generate a deterministic mock evaluation for a single case.
    Scores vary based on answer text content, simulating realistic variation.
    """
    answer = row.get("answer_text", "")
    question = row.get("question_text", "")
    q_type = row.get("question_type", "")

    per_q_scores = {}
    for dim in DIMS:
        score = _hash_to_score(answer, dim)
        # Slight boost for obviously strong signals
        if dim == "evidence_support" and len(answer) < 30:
            score = min(score, 0)  # Very short answers can't have good evidence
        if dim == "structure_clarity" and any(kw in answer for kw in ["第一", "第二", "第三", "首先", "其次", "最后"]):
            score = min(score + 1, 3)  # Structural keywords → bonus
        per_q_scores[dim] = score

    dim_summary = {}
    for dim in DIMS:
        s = per_q_scores[dim]
        dim_summary[dim] = {
            "average_score": float(s),
            "max_score": 3,
            "overall_assessment": f"Mock 评估: {DIM_LABELS[dim]}得分 {s}/3",
            "top_weakness": "Mock mode — 无具体分析",
            "top_strength": "Mock mode — 无具体分析",
        }

    weights = {"content_relevance": 0.35, "structure_clarity": 0.25,
               "evidence_support": 0.25, "expression_credibility": 0.15}
    weighted = sum(per_q_scores[d] * weights[d] for d in DIMS)

    return {
        "per_question_scores": [{
            "question_id": 1,
            "question_text": question,
            "content_relevance": {"score": per_q_scores["content_relevance"], "max_score": 3,
                "evidence": f"Mock: answer_len={len(answer)}", "deduction_points": [], "hit_points": []},
            "structure_clarity": {"score": per_q_scores["structure_clarity"], "max_score": 3,
                "evidence": f"Mock: has_structure_kw={any(kw in answer for kw in ['第一','第二','首先'])}", "deduction_points": [], "hit_points": []},
            "evidence_support": {"score": per_q_scores["evidence_support"], "max_score": 3,
                "evidence": f"Mock: answer_len={len(answer)}", "deduction_points": [], "hit_points": []},
            "expression_credibility": {"score": per_q_scores["expression_credibility"], "max_score": 3,
                "evidence": "Mock", "deduction_points": [], "hit_points": []},
        }],
        "dimension_summary": dim_summary,
        "overall_assessment": {
            "weighted_total_score": round(weighted, 2),
            "max_score": 3,
            "summary": f"Mock 评估完成。加权总分 {weighted:.2f}/3",
            "interview_performance_level": "Mock",
        },
    }


# ── Real LLM Evaluation ────────────────────────────────────────────

def _build_transcript(row: dict) -> list[dict]:
    """Build a minimal interview transcript from CSV row data."""
    transcript = [
        {"round": 0, "question_id": 1, "follow_up_depth": 0,
         "role": "interviewer", "message": row.get("question_text", "")},
        {"round": 1, "question_id": 1, "follow_up_depth": 0,
         "role": "candidate", "message": row.get("answer_text", "")},
    ]
    # Add follow-up chain if present
    fu_chain = row.get("follow_up_chain", "").strip()
    if fu_chain and fu_chain != "无追问":
        parts = fu_chain.split(";")
        for i, part in enumerate(parts):
            part = part.strip().strip("'")
            if "→" in part:
                # Split interviewer/candidate turns
                turns = [t.strip().strip("'") for t in part.split("→")]
                for j, turn in enumerate(turns):
                    if turn:
                        transcript.append({
                            "round": len(transcript),
                            "question_id": 1,
                            "follow_up_depth": (i + 1) if j == 0 else (i + 1),
                            "role": "interviewer" if j == 0 else "candidate",
                            "message": turn,
                        })
    return transcript


def _call_real_evaluator(row: dict, job_profile: dict) -> dict:
    """Call the real evaluator agent via backend service."""
    from backend.services.evaluator import get_evaluator_service
    import asyncio

    transcript = _build_transcript(row)
    question_set = {"questions": [{
        "id": 1,
        "question_text": row.get("question_text", ""),
        "type": row.get("question_type", ""),
    }]}

    svc = get_evaluator_service()
    # Override to force real mode
    svc.llm.provider = os.getenv("MODEL_PROVIDER", "openai")
    svc.llm.api_key = os.getenv("API_KEY", "")
    svc.llm.model = os.getenv("MODEL_NAME", svc.llm.model)

    if not svc.llm.api_key:
        raise RuntimeError(
            "真实 LLM 模式需要设置 API_KEY 环境变量。\n"
            "  export API_KEY=your_key_here\n"
            "  或使用 --mock 模式（默认）"
        )

    loop = asyncio.new_event_loop()
    try:
        result = loop.run_until_complete(
            svc.evaluate(job_profile=job_profile, question_set=question_set, transcript=transcript)
        )
        return result
    finally:
        loop.close()


# ── Main Evaluation Loop ───────────────────────────────────────────

def load_eval_set(path: str) -> list[dict]:
    """Load eval set CSV. Raises clear errors on any problem."""
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"评测集文件不存在: {path}\n"
            f"  请确认文件路径正确，或先创建评测集: evals/eval_set_v1.csv"
        )

    rows = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, start=2):  # line 1 is header
            # Validate required fields
            missing = []
            for field in ["eval_id", "answer_text", "question_text", "jd_category", "jd_level", "jd_text"]:
                if not row.get(field, "").strip():
                    missing.append(field)
            if missing:
                print(f"[WARN] 警告: 第{i}行 eval_id={row.get('eval_id','?')} 缺少字段: {missing}，跳过该条", file=sys.stderr)
                continue
            rows.append(row)

    if not rows:
        raise ValueError(
            f"评测集为空或所有行均缺少必要字段: {path}\n"
            f"  请检查 CSV 文件是否包含表头行和数据行。"
        )

    print(f"[OK] 加载评测集: {len(rows)} 条 case (来自 {path})")
    return rows


def run_evaluation(args: argparse.Namespace) -> None:
    """Main evaluation loop."""
    rows = load_eval_set(args.input)
    use_real = args.real

    # Check if real mode is viable
    if use_real:
        api_key = os.getenv("API_KEY", "")
        if not api_key:
            print("[WARN] 未检测到 API_KEY 环境变量，自动降级为 mock 模式", file=sys.stderr)
            print("  如需真实 LLM 评测，请设置: export API_KEY=your_key", file=sys.stderr)
            use_real = False
        else:
            # Verify backend import works
            try:
                from backend.services.evaluator import get_evaluator_service  # noqa: F401
            except ImportError as e:
                print(f"[FAIL] 无法导入 backend: {e}", file=sys.stderr)
                print("  请确保在项目根目录运行，且 backend/ 目录存在", file=sys.stderr)
                sys.exit(1)
            print(f"[OK] 真实 LLM 模式 (provider={os.getenv('MODEL_PROVIDER', 'openai')}, "
                  f"model={os.getenv('MODEL_NAME', 'default')})")

    if not use_real:
        print("[OK] Mock 模式（确定性、可复现的模拟评分）")

    # Output columns
    out_columns = [
        "eval_id", "jd_category", "jd_level",
        "ai_content_relevance", "ai_structure_clarity",
        "ai_evidence_support", "ai_expression_credibility",
        "ai_weighted_total",
        "golden_content_relevance", "golden_structure_clarity",
        "golden_evidence_support", "golden_expression_credibility",
        "golden_weighted_total",
        "eval_mode", "eval_error", "eval_duration_ms", "eval_timestamp",
    ]

    out_dir = os.path.dirname(args.output) or "."
    os.makedirs(out_dir, exist_ok=True)

    results = []
    errors = 0
    t_start = time.time()

    for idx, row in enumerate(rows):
        eval_id = row["eval_id"]
        print(f"\n[{idx+1}/{len(rows)}] {eval_id} ...", end=" ", flush=True)

        # Build job profile from CSV
        job_profile = {
            "position": {
                "title": row.get("jd_category", "未知"),
                "level": row.get("jd_level", "中级"),
            }
        }

        # Collect golden scores
        golden = {}
        for dim in DIMS:
            key = f"golden_{dim}"
            val = row.get(key, "").strip()
            golden[dim] = float(val) if val else 0.0
        weights = {"content_relevance": 0.35, "structure_clarity": 0.25,
                   "evidence_support": 0.25, "expression_credibility": 0.15}
        golden_weighted = round(sum(golden[d] * weights[d] for d in DIMS), 2)

        error_msg = ""
        ai_result: Optional[dict] = None
        t_case = time.time()

        for attempt in range(args.retries + 1):
            try:
                if use_real:
                    ai_result = _call_real_evaluator(row, job_profile)
                else:
                    ai_result = _generate_mock_evaluation(row)
                break
            except Exception as e:
                error_msg = f"[attempt {attempt+1}/{args.retries+1}] {e}"
                if attempt < args.retries:
                    print(f"重试...", end=" ", flush=True)
                    time.sleep(1)
                else:
                    errors += 1
                    print(f"[FAIL] 失败: {error_msg}", file=sys.stderr)

        duration_ms = round((time.time() - t_case) * 1000, 2)

        # Extract AI scores
        if ai_result and not error_msg:
            ai_scores = {}
            per_q = ai_result.get("per_question_scores", [{}])[0]
            for dim in DIMS:
                ai_scores[dim] = per_q.get(dim, {}).get("score", -1)
            ai_weighted = ai_result.get("overall_assessment", {}).get("weighted_total_score", -1)
            print(f"[OK] AI={ai_weighted} | Golden={golden_weighted}")
        else:
            ai_scores = {dim: -1 for dim in DIMS}
            ai_weighted = -1
            if not error_msg:
                error_msg = "AI 评分返回为空"

        results.append({
            "eval_id": eval_id,
            "jd_category": row.get("jd_category", ""),
            "jd_level": row.get("jd_level", ""),
            "ai_content_relevance": ai_scores["content_relevance"],
            "ai_structure_clarity": ai_scores["structure_clarity"],
            "ai_evidence_support": ai_scores["evidence_support"],
            "ai_expression_credibility": ai_scores["expression_credibility"],
            "ai_weighted_total": ai_weighted,
            "golden_content_relevance": golden["content_relevance"],
            "golden_structure_clarity": golden["structure_clarity"],
            "golden_evidence_support": golden["evidence_support"],
            "golden_expression_credibility": golden["expression_credibility"],
            "golden_weighted_total": golden_weighted,
            "eval_mode": "real" if use_real else "mock",
            "eval_error": error_msg,
            "eval_duration_ms": duration_ms,
            "eval_timestamp": datetime.now().isoformat(),
        })

    # ── Write output ────────────────────────────────────────────────
    with open(args.output, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=out_columns)
        writer.writeheader()
        writer.writerows(results)

    total_time = time.time() - t_start
    success_count = len([r for r in results if not r["eval_error"]])

    print(f"\n{'='*60}")
    print(f"[OK] 评测完成: {success_count}/{len(rows)} 成功, {errors} 失败")
    print(f"  耗时: {total_time:.1f}s (均 {total_time/len(rows)*1000:.0f}ms/case)")
    print(f"  模式: {'真实 LLM' if use_real else 'Mock (确定性)'}")
    print(f"  输出: {args.output}")

    if errors > 0:
        print(f"\n[WARN] {errors} 条 case 评测失败。失败详情见上方 stderr 输出和输出 CSV 的 eval_error 列。")

    if errors == len(rows):
        print("\n[FAIL] 所有 case 评测均失败，请检查:", file=sys.stderr)
        print("  1. Mock 模式: 输入 CSV 格式是否正确", file=sys.stderr)
        print("  2. 真实模式: API_KEY 是否有效、网络是否可用", file=sys.stderr)
        print(f"  3. 查看输出 CSV 的 eval_error 列获取具体错误信息: {args.output}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    args = parse_args()
    try:
        run_evaluation(args)
    except FileNotFoundError as e:
        print(f"[FAIL] 文件错误: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"[FAIL] 数据错误: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n[WARN] 用户中断", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"[FAIL] 未预期的错误:\n{traceback.format_exc()}", file=sys.stderr)
        sys.exit(1)
