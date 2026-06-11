"""
Pydantic data models for the AI Interview Training Agent.

All request/response schemas and internal data structures.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ── Session ──────────────────────────────────────────────────────────

class SessionPhase(str, Enum):
    CREATED = "created"
    JD_PARSED = "jd_parsed"
    QUESTIONS_READY = "questions_ready"
    INTERVIEWING = "interviewing"
    INTERVIEW_COMPLETE = "interview_complete"
    EVALUATED = "evaluated"
    COACHED = "coached"
    JUDGED = "judged"
    COMPLETED = "completed"
    ERROR = "error"


class SessionState(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    phase: SessionPhase = SessionPhase.CREATED
    jd_text: str = ""
    target_position: str = ""
    pressure_level: str = "moderate"
    max_rounds: int = 25
    max_follow_ups: int = 4
    job_profile: Optional[dict] = None
    question_set: Optional[dict] = None
    interview_transcript: list[dict] = Field(default_factory=list)
    evaluation_result: Optional[dict] = None
    coaching_result: Optional[dict] = None
    judge_result: Optional[dict] = None
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    error_message: str = ""


# ── JD Parser ────────────────────────────────────────────────────────

class JDParseRequest(BaseModel):
    jd_text: str = Field(..., description="原始 JD 文本")
    target_position: str = Field(default="", description="目标岗位类型（可选）")


class JDParseResponse(BaseModel):
    session_id: str
    phase: str
    job_profile: dict


# ── Questions ────────────────────────────────────────────────────────

class GenerateQuestionsRequest(BaseModel):
    pass  # 从 session 中读取 job_profile


class GenerateQuestionsResponse(BaseModel):
    session_id: str
    phase: str
    question_set: dict


# ── Interview ────────────────────────────────────────────────────────

class StartInterviewResponse(BaseModel):
    session_id: str
    phase: str
    action: str  # "ask_question"
    question_id: int
    question_number: int
    total_questions: int
    follow_up_depth: int
    message: str


class SubmitAnswerRequest(BaseModel):
    answer: str = Field(..., min_length=1, description="候选人的回答")


class SubmitAnswerResponse(BaseModel):
    session_id: str
    action: str  # "ask_question" | "follow_up" | "end_interview"
    question_id: int | None = None
    question_number: int | None = None
    total_questions: int | None = None
    follow_up_depth: int | None = None
    follow_up_reason: str | None = None
    message: str
    interview_complete: bool = False


# ── Evaluation ───────────────────────────────────────────────────────

class EvaluationResponse(BaseModel):
    session_id: str
    phase: str
    evaluation_result: dict


# ── Coaching ─────────────────────────────────────────────────────────

class CoachingResponse(BaseModel):
    session_id: str
    phase: str
    coaching_result: dict


# ── Judge ────────────────────────────────────────────────────────────

class JudgeResponse(BaseModel):
    session_id: str
    phase: str
    judge_result: dict


# ── Report ───────────────────────────────────────────────────────────

class ReportResponse(BaseModel):
    session_id: str
    phase: str
    report_markdown: str
    job_profile: dict | None = None
    evaluation_result: dict | None = None
    coaching_result: dict | None = None
    judge_result: dict | None = None
    disclaimer: str = (
        "本报告由 AI 系统自动生成，仅供面试准备参考，"
        "不构成任何形式的面试通过率承诺或保证。"
    )


# ── Full Pipeline ────────────────────────────────────────────────────

class FullPipelineRequest(BaseModel):
    jd_text: str = Field(..., description="原始 JD 文本")
    target_position: str = Field(default="", description="目标岗位类型（可选）")
    mock_answers: list[str] = Field(
        default_factory=list,
        description="模拟回答列表，用于测试模式下的全流程跑通"
    )


class FullPipelineResponse(BaseModel):
    session_id: str
    phase: str
    report: ReportResponse | None = None
    error: str = ""


# ── Health ───────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    version: str
    llm_mode: str
