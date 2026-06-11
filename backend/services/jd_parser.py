"""
JD Parser Agent Service.

Reads prompts/jd_parser_agent.md, calls LLM, returns structured JobProfile.
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
    """Load the JD Parser system prompt from prompts/jd_parser_agent.md."""
    prompt_path = PROMPTS_DIR / "jd_parser_agent.md"
    if prompt_path.exists():
        return prompt_path.read_text(encoding="utf-8")
    # Fallback: minimal inline prompt
    return """你是一位资深 HR 专家和岗位分析师。
请将以下 JD 文本解析为结构化的岗位画像 JSON。
输出格式必须包含: position, responsibilities, hard_skills, soft_skills, experience_requirements, interview_focus_areas, confidence。
仅输出合法 JSON，不要包含任何其他文字。"""


def _parse_json_response(raw: str) -> dict:
    """Extract and parse JSON from LLM response, handling markdown code blocks."""
    # Try direct parse first
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # Try extracting from markdown code block
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # Try finding JSON object with braces
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Failed to parse JSON from LLM response: {raw[:200]}...")


class JDParseService:
    """Service for parsing Job Descriptions into structured profiles."""

    def __init__(self):
        self.system_prompt = _load_prompt()
        self.llm = get_llm_client()

    async def parse(self, jd_text: str, target_position: str = "") -> dict:
        """
        Parse a raw JD text into a structured JobProfile.

        Args:
            jd_text: The raw job description text
            target_position: Optional target position type hint

        Returns:
            Structured job profile dict
        """
        user_message = f"请解析以下JD：\n\n目标岗位类型（如有）：{target_position or '未指定'}\n\nJD原文：\n{jd_text}"

        input_data = {
            "jd_text_length": len(jd_text),
            "target_position": target_position,
            "system_prompt_length": len(self.system_prompt),
        }

        error: Optional[str] = None
        result: Optional[dict] = None
        t0 = time.time()

        try:
            raw = await self.llm.chat(
                system_prompt=self.system_prompt,
                user_message=user_message,
                agent_type="jd_parser",
            )
            result = _parse_json_response(raw)
        except Exception as e:
            error = str(e)
            result = {
                "error": error,
                "position": {"title": "解析失败", "level": "未知", "inferred_category": "未知"},
                "confidence": {"overall": "low", "low_confidence_fields": ["all"], "notes": f"LLM调用失败: {error}"},
            }

        duration_ms = (time.time() - t0) * 1000

        await write_trace(
            session_id="unknown",  # Will be set by the caller
            agent_type="jd_parser",
            phase="phase1_jd_parse",
            llm_mode=self.llm.mode,
            input_data=input_data,
            output_data=result,
            duration_ms=duration_ms,
            error=error,
        )

        return result


# ── Singleton ────────────────────────────────────────────────────────

_jd_parser_service: Optional[JDParseService] = None


def get_jd_parser_service() -> JDParseService:
    global _jd_parser_service
    if _jd_parser_service is None:
        _jd_parser_service = JDParseService()
    return _jd_parser_service
