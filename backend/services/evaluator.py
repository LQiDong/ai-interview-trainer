"""
评估官 Agent Service.

Four-dimension evaluation (0-3 scale):
1. 内容匹配度 (Content Relevance) — 35%
2. 结构清晰度 (Structure Clarity) — 25%
3. 证据支撑度 (Evidence Support) — 25%
4. 表达可信度 (Expression Credibility) — 15%
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Optional

from backend.llm_client import get_llm_client
from backend.tracer import write_trace


PROMPTS_DIR = Path(__file__).resolve().parent.parent.parent / "prompts"


def _load_prompt() -> str:
    prompt_path = PROMPTS_DIR / "evaluator_agent.md"
    if prompt_path.exists():
        return prompt_path.read_text(encoding="utf-8")
    return """你是一位面试评估专家。请基于对话记录对候选人进行四维度评分（0-3分）。"""


def _parse_json_response(raw: str) -> dict:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    raise ValueError(f"Failed to parse JSON from LLM response: {raw[:200]}...")


class EvaluatorService:
    """Service for evaluating interview performance across 4 dimensions."""

    def __init__(self):
        self.system_prompt = _load_prompt()
        self.llm = get_llm_client()

    async def evaluate(
        self,
        job_profile: dict,
        question_set: dict,
        transcript: list[dict],
    ) -> dict:
        """
        Evaluate the interview transcript and return 4-dimension scores.

        Args:
            job_profile: Structured job profile from JD Parser
            question_set: Question set used in the interview
            transcript: Full interview conversation transcript

        Returns:
            Evaluation result with per-question and dimension summary scores
        """
        # Compress transcript for evaluation
        compressed = _compress_transcript(transcript)
        questions = question_set.get("questions", [])
        title = job_profile.get("position", {}).get("title", "未知岗位")
        level = job_profile.get("position", {}).get("level", "中级")

        user_message = f"""请对以下面试进行四维度评估。

岗位信息：
- 岗位：{title}
- 级别：{level}

面试题目（共{len(questions)}题）：
{json.dumps([{"id": q.get("id"), "text": q.get("question_text")} for q in questions], ensure_ascii=False, indent=2)}

对话记录：
{compressed}

请输出四维度评分 JSON。"""

        input_data = {
            "job_title": title,
            "job_level": level,
            "question_count": len(questions),
            "transcript_rounds": len(transcript),
            "compressed_length": len(compressed),
        }

        error: Optional[str] = None
        result: Optional[dict] = None
        t0 = time.time()

        try:
            raw = await self.llm.chat(
                system_prompt=self.system_prompt,
                user_message=user_message,
                agent_type="evaluator",
                context={"total_questions": len(questions)},
            )
            result = _parse_json_response(raw)
            # Validate the result
            result = _validate_evaluation(result, len(questions))
        except Exception as e:
            error = str(e)
            result = _fallback_evaluation(questions, transcript)

        duration_ms = (time.time() - t0) * 1000

        await write_trace(
            session_id="unknown",
            agent_type="evaluator",
            phase="phase4_evaluation",
            llm_mode=self.llm.mode,
            input_data=input_data,
            output_data=result,
            duration_ms=duration_ms,
            error=error,
        )

        return result


def _compress_transcript(transcript: list[dict]) -> str:
    """Compress transcript to key Q&A pairs for evaluation."""
    lines = []
    for i, entry in enumerate(transcript):
        role = "面试官" if entry.get("role") == "interviewer" else "候选人"
        msg = entry.get("message", "")
        # Truncate very long messages
        if len(msg) > 500:
            msg = msg[:500] + "..."
        qid = entry.get("question_id", "?")
        depth = entry.get("follow_up_depth", 0)
        lines.append(f"[轮{i+1}][Q{qid}][深度{depth}][{role}] {msg}")
    return "\n".join(lines)


def _validate_evaluation(result: dict, total_questions: int) -> dict:
    """Validate and fix evaluation result structure."""
    # Ensure per_question_scores exists
    if "per_question_scores" not in result or not result["per_question_scores"]:
        result["per_question_scores"] = []

    # Ensure dimension_summary exists
    if "dimension_summary" not in result:
        result["dimension_summary"] = {
            "content_relevance": {"average_score": 0, "max_score": 3, "overall_assessment": "", "top_weakness": "", "top_strength": ""},
            "structure_clarity": {"average_score": 0, "max_score": 3, "overall_assessment": "", "top_weakness": "", "top_strength": ""},
            "evidence_support": {"average_score": 0, "max_score": 3, "overall_assessment": "", "top_weakness": "", "top_strength": ""},
            "expression_credibility": {"average_score": 0, "max_score": 3, "overall_assessment": "", "top_weakness": "", "top_strength": ""},
        }

    # Ensure overall_assessment exists
    if "overall_assessment" not in result:
        result["overall_assessment"] = {"weighted_total_score": 0, "max_score": 3, "summary": "", "interview_performance_level": ""}

    # Calculate dimension averages from per_question_scores
    dims = ["content_relevance", "structure_clarity", "evidence_support", "expression_credibility"]
    for dim in dims:
        scores = [
            q.get(dim, {}).get("score", 0)
            for q in result["per_question_scores"]
        ]
        if scores:
            avg = round(sum(scores) / len(scores), 2)
            result["dimension_summary"][dim]["average_score"] = avg

    # Calculate weighted total
    weights = {"content_relevance": 0.35, "structure_clarity": 0.25, "evidence_support": 0.25, "expression_credibility": 0.15}
    weighted = sum(
        result["dimension_summary"][dim].get("average_score", 0) * weight
        for dim, weight in weights.items()
    )
    result["overall_assessment"]["weighted_total_score"] = round(weighted, 2)

    return result


def _fallback_evaluation(questions: list[dict], transcript: list[dict]) -> dict:
    """Generate a minimal fallback evaluation when LLM fails."""
    return {
        "evaluation_meta": {
            "position_level_anchor": "中级",
            "total_questions_evaluated": len(questions),
            "evaluation_timestamp": "",
            "note": "Fallback evaluation due to LLM error"
        },
        "per_question_scores": [],
        "dimension_summary": {
            "content_relevance": {"average_score": 0, "max_score": 3, "overall_assessment": "评估服务暂时不可用", "top_weakness": "", "top_strength": ""},
            "structure_clarity": {"average_score": 0, "max_score": 3, "overall_assessment": "评估服务暂时不可用", "top_weakness": "", "top_strength": ""},
            "evidence_support": {"average_score": 0, "max_score": 3, "overall_assessment": "评估服务暂时不可用", "top_weakness": "", "top_strength": ""},
            "expression_credibility": {"average_score": 0, "max_score": 3, "overall_assessment": "评估服务暂时不可用", "top_weakness": "", "top_strength": ""},
        },
        "overall_assessment": {"weighted_total_score": 0, "max_score": 3, "summary": "评估服务暂时不可用，请稍后重试。", "interview_performance_level": "未知"},
    }


# ── Singleton ────────────────────────────────────────────────────────

_evaluator_service: Optional[EvaluatorService] = None


def get_evaluator_service() -> EvaluatorService:
    global _evaluator_service
    if _evaluator_service is None:
        _evaluator_service = EvaluatorService()
    return _evaluator_service
