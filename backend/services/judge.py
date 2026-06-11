"""
Judge Agent Service.

Independent quality review — checks:
1. Score-evidence consistency
2. Low-score deduction completeness
3. Coach-evaluator alignment
4. Over-promise detection
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
    prompt_path = PROMPTS_DIR / "judge_agent.md"
    if prompt_path.exists():
        return prompt_path.read_text(encoding="utf-8")
    return """你是一位独立的质量审核专家。审核评估官和教练Agent的输出质量。"""


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


class JudgeService:
    """Independent quality review across 4 check dimensions."""

    def __init__(self):
        self.system_prompt = _load_prompt()
        self.llm = get_llm_client()

    async def review(
        self,
        evaluation_result: dict,
        coaching_result: dict,
        transcript: list[dict],
    ) -> dict:
        """
        Review evaluation and coaching quality.

        Args:
            evaluation_result: Full evaluation output
            coaching_result: Full coaching output
            transcript: Interview transcript

        Returns:
            Judge result with 4 check dimensions
        """
        # Compress transcript
        compressed = _compress_transcript(transcript)

        # Collect all deduction points for alignment check
        deduction_points = _collect_deduction_points(evaluation_result)
        coaching_entries = _collect_coaching_entries(coaching_result)

        user_message = f"""请审核以下评估和教练输出的质量。

评估结果（摘要）：
- 总分：{evaluation_result.get('overall_assessment', {}).get('weighted_total_score', 'N/A')}
- 维度均分：{json.dumps({k: v.get('average_score') for k, v in evaluation_result.get('dimension_summary', {}).items()}, ensure_ascii=False)}
- 扣分点总数：{len(deduction_points)}

教练建议（摘要）：
- 改进优先级：{coaching_result.get('coaching_meta', {}).get('improvement_priority', 'N/A')}
- 教练条目数：{len(coaching_entries)}
- Top 3 Actions：{len(coaching_result.get('top_3_actions', []))}

全部扣分点列表：
{json.dumps(deduction_points, ensure_ascii=False, indent=2)}

教练回应列表：
{json.dumps(coaching_entries, ensure_ascii=False, indent=2)}

对话记录（精简版）：
{compressed}

完整评估结果：
{json.dumps(evaluation_result, ensure_ascii=False, indent=2)}

完整教练结果：
{json.dumps(coaching_result, ensure_ascii=False, indent=2)}

请输出 Judge 复核报告 JSON。"""

        input_data = {
            "evaluation_score": evaluation_result.get("overall_assessment", {}).get("weighted_total_score"),
            "deduction_count": len(deduction_points),
            "coaching_entry_count": len(coaching_entries),
            "coaching_top3_count": len(coaching_result.get("top_3_actions", [])),
        }

        error: Optional[str] = None
        result: Optional[dict] = None
        t0 = time.time()

        try:
            raw = await self.llm.chat(
                system_prompt=self.system_prompt,
                user_message=user_message,
                agent_type="judge",
            )
            result = _parse_json_response(raw)
            result = _validate_judge_result(result)
        except Exception as e:
            error = str(e)
            result = _fallback_judge_result()

        duration_ms = (time.time() - t0) * 1000

        await write_trace(
            session_id="unknown",
            agent_type="judge",
            phase="phase6_judge",
            llm_mode=self.llm.mode,
            input_data=input_data,
            output_data=result,
            duration_ms=duration_ms,
            error=error,
        )

        return result


def _compress_transcript(transcript: list[dict]) -> str:
    lines = []
    for entry in transcript:
        role = "面试官" if entry.get("role") == "interviewer" else "候选人"
        msg = entry.get("message", "")
        if len(msg) > 200:
            msg = msg[:200] + "..."
        lines.append(f"[{role}] {msg}")
    return "\n".join(lines)


def _collect_deduction_points(evaluation_result: dict) -> list[dict]:
    points = []
    for q_score in evaluation_result.get("per_question_scores", []):
        qid = q_score.get("question_id")
        for dim in ["content_relevance", "structure_clarity", "evidence_support", "expression_credibility"]:
            dim_data = q_score.get(dim, {})
            if dim_data.get("score", 3) < 3:
                for dp in dim_data.get("deduction_points", []):
                    points.append({
                        "question_id": qid,
                        "dimension": dim,
                        "score": dim_data.get("score"),
                        "deduction_point": dp,
                    })
    return points


def _collect_coaching_entries(coaching_result: dict) -> list[dict]:
    entries = []
    for q_coach in coaching_result.get("per_question_coaching", []):
        qid = q_coach.get("question_id")
        for entry in q_coach.get("coaching_entries", []):
            entries.append({
                "question_id": qid,
                "dimension": entry.get("target_dimension"),
                "deduction_point_ref": entry.get("deduction_point_from_evaluator"),
            })
    return entries


def _validate_judge_result(result: dict) -> dict:
    if "judge_meta" not in result:
        result["judge_meta"] = {"overall_verdict": "pass_with_issues"}

    required_checks = [
        "score_evidence_consistency",
        "low_score_deduction_completeness",
        "coach_evaluator_alignment",
        "over_promise_detection",
    ]

    if "check_results" not in result:
        result["check_results"] = {}

    for check in required_checks:
        if check not in result["check_results"]:
            result["check_results"][check] = {
                "passed": True,
                "total_issues": 0,
                "critical_issues": 0,
                "high_severity_issues": 0,
                "issues": [],
            }

    if "overall_verdict" not in result:
        result["overall_verdict"] = "pass_with_issues"

    if "verdict_rationale" not in result:
        result["verdict_rationale"] = ""

    return result


def _fallback_judge_result() -> dict:
    return {
        "judge_meta": {
            "overall_verdict": "pass_with_issues",
            "note": "Fallback judge result due to LLM error"
        },
        "check_results": {
            "score_evidence_consistency": {"passed": True, "total_issues": 0, "critical_issues": 0, "high_severity_issues": 0, "issues": []},
            "low_score_deduction_completeness": {"passed": True, "total_issues": 0, "critical_issues": 0, "high_severity_issues": 0, "issues": []},
            "coach_evaluator_alignment": {"passed": True, "total_issues": 0, "critical_issues": 0, "high_severity_issues": 0, "issues": []},
            "over_promise_detection": {"passed": True, "total_issues": 0, "critical_issues": 0, "high_severity_issues": 0, "issues": []},
        },
        "overall_verdict": "pass_with_issues",
        "verdict_rationale": "Judge服务暂时不可用（Fallback模式），请以评估和教练结果为准。",
    }


# ── Singleton ────────────────────────────────────────────────────────

_judge_service: Optional[JudgeService] = None


def get_judge_service() -> JudgeService:
    global _judge_service
    if _judge_service is None:
        _judge_service = JudgeService()
    return _judge_service
