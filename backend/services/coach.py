"""
教练 Agent Service.

Generates actionable improvement suggestions, each mapped to a specific
deduction point from the evaluator.
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
    prompt_path = PROMPTS_DIR / "coach_agent.md"
    if prompt_path.exists():
        return prompt_path.read_text(encoding="utf-8")
    return """你是一位面试教练。基于评估官的评分结果，为候选人提供可行动的改进建议。每条建议必须对应评估官的扣分点。"""


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


class CoachService:
    """Service for generating coaching suggestions mapped to evaluator deductions."""

    def __init__(self):
        self.system_prompt = _load_prompt()
        self.llm = get_llm_client()

    async def generate_coaching(
        self,
        evaluation_result: dict,
        transcript: list[dict],
        job_profile: dict,
    ) -> dict:
        """
        Generate coaching suggestions based on evaluation results.

        Each coaching entry MUST reference a specific deduction_point
        from the evaluator's per_question_scores.

        Args:
            evaluation_result: Full evaluation output from EvaluatorService
            transcript: Interview conversation transcript
            job_profile: Structured job profile

        Returns:
            Coaching result with per-question suggestions and top-3 actions
        """
        # Collect all deduction points for the coach to address
        deduction_map = _collect_deduction_points(evaluation_result)

        # Compress transcript
        compressed = _compress_transcript_for_coach(transcript)

        user_message = f"""请基于以下评估结果生成教练建议。

岗位：{job_profile.get('position', {}).get('title', '未知')}

评估结果：
{json.dumps(evaluation_result, ensure_ascii=False, indent=2)}

所有需回应的扣分点：
{json.dumps(deduction_map, ensure_ascii=False, indent=2)}

对话记录（精简版）：
{compressed}

请输出教练建议 JSON。每一条 coaching_entry 必须对应上面列出的扣分点。"""

        input_data = {
            "evaluation_dimensions": list(evaluation_result.get("dimension_summary", {}).keys()),
            "total_deduction_points": len(deduction_map),
            "transcript_rounds": len(transcript),
        }

        error: Optional[str] = None
        result: Optional[dict] = None
        t0 = time.time()

        try:
            raw = await self.llm.chat(
                system_prompt=self.system_prompt,
                user_message=user_message,
                agent_type="coach",
            )
            result = _parse_json_response(raw)
            result = _validate_coaching(result, deduction_map)
        except Exception as e:
            error = str(e)
            result = _fallback_coaching(evaluation_result, deduction_map)

        duration_ms = (time.time() - t0) * 1000

        await write_trace(
            session_id="unknown",
            agent_type="coach",
            phase="phase5_coaching",
            llm_mode=self.llm.mode,
            input_data=input_data,
            output_data=result,
            duration_ms=duration_ms,
            error=error,
        )

        return result


def _collect_deduction_points(evaluation_result: dict) -> list[dict]:
    """Collect all deduction points that the coach must address."""
    points = []
    for q_score in evaluation_result.get("per_question_scores", []):
        qid = q_score.get("question_id")
        for dim in ["content_relevance", "structure_clarity", "evidence_support", "expression_credibility"]:
            dim_data = q_score.get(dim, {})
            for dp in dim_data.get("deduction_points", []):
                points.append({
                    "question_id": qid,
                    "dimension": dim,
                    "score": dim_data.get("score"),
                    "deduction_point": dp,
                })
    return points


def _compress_transcript_for_coach(transcript: list[dict]) -> str:
    """Create a concise transcript for the coach."""
    lines = []
    for entry in transcript:
        role = "面试官" if entry.get("role") == "interviewer" else "候选人"
        msg = entry.get("message", "")
        if len(msg) > 300:
            msg = msg[:300] + "..."
        lines.append(f"[{role}] {msg}")
    return "\n".join(lines)


def _validate_coaching(result: dict, deduction_map: list[dict]) -> dict:
    """Validate and fix coaching result structure."""
    if "coaching_meta" not in result:
        result["coaching_meta"] = {"improvement_priority": "evidence_support", "priority_rationale": "", "total_action_items": 0}

    if "per_question_coaching" not in result:
        result["per_question_coaching"] = []

    if "top_3_actions" not in result:
        result["top_3_actions"] = []

    if "dimension_improvement_plan" not in result:
        result["dimension_improvement_plan"] = {}

    if "general_advice" not in result:
        result["general_advice"] = ""

    return result


def _fallback_coaching(evaluation_result: dict, deduction_map: list[dict]) -> dict:
    """Generate minimal fallback coaching result."""
    return {
        "coaching_meta": {
            "improvement_priority": "evidence_support",
            "priority_rationale": "基于评估结果推断（Fallback模式）",
            "total_action_items": len(deduction_map),
            "note": "Fallback coaching due to LLM error"
        },
        "per_question_coaching": [],
        "top_3_actions": [
            {
                "rank": 1,
                "action": "加强量化表达——每次回答用数据支撑观点",
                "target_dimension": "evidence_support",
                "expected_impact": "可提升证据支撑度得分",
                "practice_method": "准备项目案例时强制填写基线、动作、变化、归因",
                "time_estimate": "2周"
            }
        ],
        "dimension_improvement_plan": {},
        "general_advice": "教练服务暂时不可用，请稍后重试获取详细建议。",
    }


# ── Singleton ────────────────────────────────────────────────────────

_coach_service: Optional[CoachService] = None


def get_coach_service() -> CoachService:
    global _coach_service
    if _coach_service is None:
        _coach_service = CoachService()
    return _coach_service
