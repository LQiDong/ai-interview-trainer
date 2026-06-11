"""
面试官 Agent Service.

Conducts multi-turn interview dialogue with follow-up questioning.
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
    prompt_path = PROMPTS_DIR / "interviewer_agent.md"
    if prompt_path.exists():
        return prompt_path.read_text(encoding="utf-8")
    return """你是一位 AI 产品方向面试官。请根据面试题和候选人的回答，决定追问还是换题。输出 JSON 格式的面试官动作。"""


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


class InterviewerService:
    """Service for conducting the interview conversation."""

    def __init__(self):
        self.system_prompt = _load_prompt()
        self.llm = get_llm_client()

    async def get_first_question(
        self,
        job_profile: dict,
        question_set: dict,
        pressure_level: str = "moderate",
        max_rounds: int = 25,
        max_follow_ups: int = 4,
    ) -> dict:
        """Get the first interview question."""
        questions = question_set.get("questions", [])
        if not questions:
            # Generate generic questions if question_set is empty
            questions = _generate_generic_questions(job_profile)
            question_set = {"questions": questions}

        first_q = questions[0]
        result = {
            "action": "ask_question",
            "question_id": first_q.get("id", 1),
            "question_number": 1,
            "total_questions": len(questions),
            "follow_up_depth": 0,
            "message": first_q.get("question_text", "请做一下自我介绍。"),
        }
        return result

    async def process_answer(
        self,
        job_profile: dict,
        question_set: dict,
        transcript: list[dict],
        current_question_index: int,
        current_follow_up_depth: int,
        candidate_answer: str,
        pressure_level: str = "moderate",
        max_rounds: int = 25,
        max_follow_ups: int = 4,
    ) -> dict:
        """
        Process the candidate's answer and decide the next action.

        Returns an interviewer action dict:
          {"action": "follow_up", "question_id": N, "follow_up_depth": D, ...}
          {"action": "ask_question", "question_id": N, ...}
          {"action": "end_interview", ...}
        """
        questions = question_set.get("questions", [])
        if not questions:
            questions = _generate_generic_questions(job_profile)

        total_questions = len(questions)

        # Build the user message for the LLM
        transcript_text = _format_transcript(transcript)
        current_q = (
            questions[current_question_index]
            if current_question_index < len(questions)
            else {"question_text": "面试结束"}
        )

        user_message = f"""当前面试状态：
岗位：{job_profile.get('position', {}).get('title', '未知')}
压力等级：{pressure_level}
最大追问层数：{max_follow_ups}

当前题目（第{current_question_index + 1}题，共{total_questions}题）：
{current_q.get('question_text', '')}

追问深度：第{current_follow_up_depth}层

对话记录：
{transcript_text}

候选人最新回答：
{candidate_answer}

请根据追问决策逻辑，输出下一步行动 JSON。"""

        context = {
            "transcript": transcript,
            "current_question_index": current_question_index,
            "total_questions": total_questions,
            "current_follow_up_depth": current_follow_up_depth,
        }

        input_data = {
            "current_question_index": current_question_index,
            "current_follow_up_depth": current_follow_up_depth,
            "transcript_length": len(transcript),
            "candidate_answer_length": len(candidate_answer),
        }

        error: Optional[str] = None
        result: Optional[dict] = None
        t0 = time.time()

        try:
            raw = await self.llm.chat(
                system_prompt=self.system_prompt,
                user_message=user_message,
                agent_type="interviewer",
                context=context,
            )
            result = _parse_json_response(raw)
        except Exception as e:
            error = str(e)
            result = _fallback_interviewer_action(
                current_question_index, current_follow_up_depth,
                total_questions, max_follow_ups
            )

        duration_ms = (time.time() - t0) * 1000

        await write_trace(
            session_id="unknown",
            agent_type="interviewer",
            phase="phase3_interview",
            llm_mode=self.llm.mode,
            input_data=input_data,
            output_data=result,
            duration_ms=duration_ms,
            error=error,
        )

        return result


def _format_transcript(transcript: list[dict]) -> str:
    """Format transcript for the LLM prompt."""
    lines = []
    for entry in transcript[-10:]:  # Last 10 rounds for context window
        role = "面试官" if entry.get("role") == "interviewer" else "候选人"
        lines.append(f"[{role}] Q{entry.get('question_id', '?')}: {entry.get('message', '')}")
    return "\n".join(lines)


def _generate_generic_questions(job_profile: dict) -> list[dict]:
    """Generate generic questions when question_set is empty."""
    title = job_profile.get("position", {}).get("title", "产品经理")
    return [
        {"id": 1, "type": "behavioral", "difficulty": "medium", "dimension": "经验匹配",
         "question_text": f"请做一个自我介绍，重点说说你在{title}方向的经验和项目。",
         "follow_up_tree": [], "reference_answer_points": []},
        {"id": 2, "type": "case_study", "difficulty": "medium", "dimension": "问题解决",
         "question_text": "请描述你在工作中遇到的最复杂的一个问题，以及你是如何解决的。",
         "follow_up_tree": [], "reference_answer_points": []},
        {"id": 3, "type": "knowledge", "difficulty": "medium", "dimension": "专业深度",
         "question_text": "你如何理解AI产品经理的核心能力？和传统产品经理有什么不同？",
         "follow_up_tree": [], "reference_answer_points": []},
        {"id": 4, "type": "case_study", "difficulty": "medium", "dimension": "数据驱动",
         "question_text": "请描述一个你通过数据驱动产品决策的具体案例。",
         "follow_up_tree": [], "reference_answer_points": []},
        {"id": 5, "type": "situational", "difficulty": "medium", "dimension": "沟通协作",
         "question_text": "当你和技术团队对产品方向有分歧时，你会如何处理？",
         "follow_up_tree": [], "reference_answer_points": []},
        {"id": 6, "type": "knowledge", "difficulty": "hard", "dimension": "专业知识",
         "question_text": "你如何评估一个AI产品的质量？请给出你的评估框架。",
         "follow_up_tree": [], "reference_answer_points": []},
        {"id": 7, "type": "behavioral", "difficulty": "medium", "dimension": "综合",
         "question_text": "请用3分钟说服我们，为什么你是这个岗位的合适人选。",
         "follow_up_tree": [], "reference_answer_points": []},
    ]


def _fallback_interviewer_action(
    current_question_index: int,
    current_follow_up_depth: int,
    total_questions: int,
    max_follow_ups: int,
) -> dict:
    """Generate fallback interviewer action when LLM fails."""
    if current_follow_up_depth < max_follow_ups - 1:
        return {
            "action": "follow_up",
            "question_id": current_question_index + 1,
            "follow_up_depth": current_follow_up_depth + 1,
            "follow_up_reason": "想要进一步了解你的思考过程",
            "message": "能否展开说说你在这个过程中的具体思考和决策？",
        }
    next_idx = current_question_index + 1
    if next_idx >= total_questions:
        return {
            "action": "end_interview",
            "summary": {"total_questions_asked": total_questions, "total_rounds": 0},
            "message": "好的，我们的面试到这里就结束了。接下来系统将为你生成评估报告。",
        }
    return {
        "action": "ask_question",
        "question_id": next_idx + 1,
        "question_number": next_idx + 1,
        "total_questions": total_questions,
        "follow_up_depth": 0,
        "message": f"接下来是第{next_idx + 1}题。",
    }


# ── Singleton ────────────────────────────────────────────────────────

_interviewer_service: Optional[InterviewerService] = None


def get_interviewer_service() -> InterviewerService:
    global _interviewer_service
    if _interviewer_service is None:
        _interviewer_service = InterviewerService()
    return _interviewer_service
