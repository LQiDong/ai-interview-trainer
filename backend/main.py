"""
AI 面试训练 Agent — FastAPI Backend MVP

No auth, no database, no payments. Mock LLM mode by default.

Run:  cd backend && uvicorn main:app --reload --port 8000
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.models import (
    SessionPhase,
    SessionState,
    JDParseRequest,
    JDParseResponse,
    GenerateQuestionsResponse,
    StartInterviewResponse,
    SubmitAnswerRequest,
    SubmitAnswerResponse,
    EvaluationResponse,
    CoachingResponse,
    JudgeResponse,
    ReportResponse,
    HealthResponse,
    FullPipelineRequest,
    FullPipelineResponse,
)
from backend.services.jd_parser import get_jd_parser_service
from backend.services.interviewer import get_interviewer_service
from backend.services.evaluator import get_evaluator_service
from backend.services.coach import get_coach_service
from backend.services.judge import get_judge_service
from backend.llm_client import get_llm_client
from backend.tracer import write_trace, get_traces
from backend.tracer import get_traces

app = FastAPI(
    title="AI 面试训练 Agent",
    version="1.0.0",
    description="Multi-Agent interview training system — MVP",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── In-memory session store (MVP) ───────────────────────────────────

sessions: dict[str, SessionState] = {}


def _get_session(session_id: str) -> SessionState:
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    return sessions[session_id]


# ── Health ───────────────────────────────────────────────────────────

@app.get("/api/health", response_model=HealthResponse)
async def health():
    llm = get_llm_client()
    return HealthResponse(status="ok", version="1.0.0", llm_mode=llm.mode)


# ── Session ──────────────────────────────────────────────────────────

@app.post("/api/sessions")
async def create_session():
    session = SessionState()
    sessions[session.session_id] = session
    await write_trace(
        session_id=session.session_id,
        agent_type="orchestrator",
        phase="phase0_init",
        llm_mode=get_llm_client().mode,
        input_data={},
        output_data={"session_id": session.session_id},
        duration_ms=0,
    )
    return {"session_id": session.session_id, "phase": session.phase}


@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    session = _get_session(session_id)
    return {
        "session_id": session.session_id,
        "phase": session.phase,
        "created_at": session.created_at,
    }


# ── Phase 1: JD Parse ────────────────────────────────────────────────

@app.post("/api/sessions/{session_id}/parse-jd", response_model=JDParseResponse)
async def parse_jd(session_id: str, req: JDParseRequest):
    session = _get_session(session_id)
    session.jd_text = req.jd_text
    session.target_position = req.target_position

    svc = get_jd_parser_service()
    job_profile = await svc.parse(req.jd_text, req.target_position)

    session.job_profile = job_profile
    session.phase = SessionPhase.JD_PARSED

    # Re-write trace with session_id
    await write_trace(
        session_id=session_id,
        agent_type="jd_parser",
        phase="phase1_jd_parse",
        llm_mode=get_llm_client().mode,
        input_data={"jd_length": len(req.jd_text)},
        output_data=job_profile,
        duration_ms=0,
    )

    return JDParseResponse(
        session_id=session_id,
        phase=session.phase,
        job_profile=job_profile,
    )


# ── Phase 2: Generate Questions ──────────────────────────────────────

@app.post("/api/sessions/{session_id}/questions", response_model=GenerateQuestionsResponse)
async def generate_questions(session_id: str):
    session = _get_session(session_id)
    if not session.job_profile:
        raise HTTPException(status_code=400, detail="请先解析 JD")

    # Generate questions based on job profile
    from backend.services.interviewer import _generate_generic_questions
    questions = _generate_generic_questions(session.job_profile)
    question_set = {"questions": questions}

    session.question_set = question_set
    session.phase = SessionPhase.QUESTIONS_READY

    await write_trace(
        session_id=session_id,
        agent_type="question_designer",
        phase="phase2_questions",
        llm_mode=get_llm_client().mode,
        input_data={"job_profile": session.job_profile},
        output_data={"question_count": len(questions)},
        duration_ms=0,
    )

    return GenerateQuestionsResponse(
        session_id=session_id,
        phase=session.phase,
        question_set=question_set,
    )


# ── Phase 3: Interview ───────────────────────────────────────────────

@app.post("/api/sessions/{session_id}/start", response_model=StartInterviewResponse)
async def start_interview(session_id: str):
    session = _get_session(session_id)
    if not session.question_set:
        raise HTTPException(status_code=400, detail="请先生成面试题")

    svc = get_interviewer_service()
    result = await svc.get_first_question(
        job_profile=session.job_profile or {},
        question_set=session.question_set,
        pressure_level=session.pressure_level,
        max_rounds=session.max_rounds,
        max_follow_ups=session.max_follow_ups,
    )

    session.phase = SessionPhase.INTERVIEWING
    session.interview_transcript.append({
        "round": 0,
        "question_id": result.get("question_id"),
        "follow_up_depth": 0,
        "role": "interviewer",
        "message": result.get("message", ""),
    })

    return StartInterviewResponse(
        session_id=session_id,
        phase=session.phase,
        action=result.get("action", "ask_question"),
        question_id=result.get("question_id", 1),
        question_number=result.get("question_number", 1),
        total_questions=result.get("total_questions", 7),
        follow_up_depth=result.get("follow_up_depth", 0),
        message=result.get("message", ""),
    )


@app.post("/api/sessions/{session_id}/answer", response_model=SubmitAnswerResponse)
async def submit_answer(session_id: str, req: SubmitAnswerRequest):
    session = _get_session(session_id)
    if session.phase != SessionPhase.INTERVIEWING:
        raise HTTPException(status_code=400, detail="面试未在进行中")

    # Record the candidate's answer
    last_q = session.interview_transcript[-1] if session.interview_transcript else {}
    round_num = len(session.interview_transcript)
    session.interview_transcript.append({
        "round": round_num,
        "question_id": last_q.get("question_id"),
        "follow_up_depth": last_q.get("follow_up_depth", 0),
        "role": "candidate",
        "message": req.answer,
    })

    # Determine current question index and follow-up depth
    current_q_idx = (last_q.get("question_id", 1) or 1) - 1
    current_fu_depth = last_q.get("follow_up_depth", 0)

    svc = get_interviewer_service()
    result = await svc.process_answer(
        job_profile=session.job_profile or {},
        question_set=session.question_set or {},
        transcript=session.interview_transcript,
        current_question_index=current_q_idx,
        current_follow_up_depth=current_fu_depth,
        candidate_answer=req.answer,
        pressure_level=session.pressure_level,
        max_rounds=session.max_rounds,
        max_follow_ups=session.max_follow_ups,
    )

    action = result.get("action", "end_interview")
    is_complete = action == "end_interview"

    # Record interviewer response
    if not is_complete:
        session.interview_transcript.append({
            "round": len(session.interview_transcript),
            "question_id": result.get("question_id"),
            "follow_up_depth": result.get("follow_up_depth", 0),
            "role": "interviewer",
            "message": result.get("message", ""),
        })
    else:
        session.phase = SessionPhase.INTERVIEW_COMPLETE

    # Check max rounds
    if len(session.interview_transcript) >= session.max_rounds * 2:
        session.phase = SessionPhase.INTERVIEW_COMPLETE
        is_complete = True
        result["message"] = "已达到最大对话轮次，面试结束。"

    return SubmitAnswerResponse(
        session_id=session_id,
        action=action,
        question_id=result.get("question_id"),
        question_number=result.get("question_number"),
        total_questions=result.get("total_questions"),
        follow_up_depth=result.get("follow_up_depth"),
        follow_up_reason=result.get("follow_up_reason"),
        message=result.get("message", ""),
        interview_complete=is_complete,
    )


# ── Phase 4: Evaluation ──────────────────────────────────────────────

@app.post("/api/sessions/{session_id}/evaluate", response_model=EvaluationResponse)
async def evaluate(session_id: str):
    session = _get_session(session_id)
    if not session.interview_transcript:
        raise HTTPException(status_code=400, detail="无对话记录")

    svc = get_evaluator_service()
    result = await svc.evaluate(
        job_profile=session.job_profile or {},
        question_set=session.question_set or {},
        transcript=session.interview_transcript,
    )

    session.evaluation_result = result
    session.phase = SessionPhase.EVALUATED

    await write_trace(
        session_id=session_id,
        agent_type="evaluator",
        phase="phase4_evaluation",
        llm_mode=get_llm_client().mode,
        input_data={"transcript_rounds": len(session.interview_transcript)},
        output_data={"weighted_total": result.get("overall_assessment", {}).get("weighted_total_score")},
        duration_ms=0,
    )

    return EvaluationResponse(
        session_id=session_id,
        phase=session.phase,
        evaluation_result=result,
    )


# ── Phase 5: Coaching ────────────────────────────────────────────────

@app.post("/api/sessions/{session_id}/coach", response_model=CoachingResponse)
async def coach(session_id: str):
    session = _get_session(session_id)
    if not session.evaluation_result:
        raise HTTPException(status_code=400, detail="请先完成评估")

    svc = get_coach_service()
    result = await svc.generate_coaching(
        evaluation_result=session.evaluation_result,
        transcript=session.interview_transcript,
        job_profile=session.job_profile or {},
    )

    session.coaching_result = result
    session.phase = SessionPhase.COACHED

    await write_trace(
        session_id=session_id,
        agent_type="coach",
        phase="phase5_coaching",
        llm_mode=get_llm_client().mode,
        input_data={},
        output_data={"top_actions": len(result.get("top_3_actions", []))},
        duration_ms=0,
    )

    return CoachingResponse(
        session_id=session_id,
        phase=session.phase,
        coaching_result=result,
    )


# ── Phase 6: Judge ───────────────────────────────────────────────────

@app.post("/api/sessions/{session_id}/judge", response_model=JudgeResponse)
async def judge(session_id: str):
    session = _get_session(session_id)
    if not session.evaluation_result or not session.coaching_result:
        raise HTTPException(status_code=400, detail="请先完成评估和教练建议")

    svc = get_judge_service()
    result = await svc.review(
        evaluation_result=session.evaluation_result,
        coaching_result=session.coaching_result,
        transcript=session.interview_transcript,
    )

    session.judge_result = result
    session.phase = SessionPhase.JUDGED

    await write_trace(
        session_id=session_id,
        agent_type="judge",
        phase="phase6_judge",
        llm_mode=get_llm_client().mode,
        input_data={},
        output_data={"verdict": result.get("overall_verdict")},
        duration_ms=0,
    )

    return JudgeResponse(
        session_id=session_id,
        phase=session.phase,
        judge_result=result,
    )


# ── Phase 7: Report ─────────────────────────────────────────────────

@app.get("/api/sessions/{session_id}/report", response_model=ReportResponse)
async def get_report(session_id: str):
    session = _get_session(session_id)

    report = ReportResponse(
        session_id=session_id,
        phase=session.phase,
        report_markdown="",
        job_profile=session.job_profile,
        evaluation_result=session.evaluation_result,
        coaching_result=session.coaching_result,
        judge_result=session.judge_result,
    )

    session.phase = SessionPhase.COMPLETED
    return report


# ── Full Pipeline (convenience) ──────────────────────────────────────

@app.post("/api/sessions/{session_id}/full-pipeline", response_model=FullPipelineResponse)
async def full_pipeline(session_id: str, req: FullPipelineRequest):
    """Run the full pipeline with mock answers for testing."""
    try:
        # Create or reuse session
        if session_id not in sessions:
            session = SessionState(session_id=session_id)
            sessions[session_id] = session
        else:
            session = sessions[session_id]

        session.jd_text = req.jd_text
        session.target_position = req.target_position

        # Phase 1: JD Parse
        svc = get_jd_parser_service()
        session.job_profile = await svc.parse(req.jd_text, req.target_position)
        session.phase = SessionPhase.JD_PARSED

        # Phase 2: Questions
        from backend.services.interviewer import _generate_generic_questions
        questions = _generate_generic_questions(session.job_profile)
        session.question_set = {"questions": questions}
        session.phase = SessionPhase.QUESTIONS_READY

        # Phase 3: Mock interview
        mock_answers = req.mock_answers or [
            "我在AI产品方向有3年经验，参与过Agent平台从0到1的建设。",
            "最复杂的问题是Agent工具调用的可靠性保障。我们发现用户反馈工具经常调用失败...",
            "Multi-Agent协作的核心是通信协议和任务分配。我认为好的Agent产品应该...",
            "我们通过A/B测试发现，优化工具调用的参数校验后成功率提升了30%...",
            "我会先理解工程团队的顾虑，然后用数据和用户反馈说话...",
            "评估AI产品UX质量需要考虑准确性、响应速度、可解释性等维度...",
            "我适合这个岗位因为我有Agent产品实操经验、数据驱动思维和跨团队协作能力。",
        ]

        interviewer_svc = get_interviewer_service()
        questions_list = questions
        session.interview_transcript = []

        for q_idx, q in enumerate(questions_list):
            # Interviewer asks
            session.interview_transcript.append({
                "round": len(session.interview_transcript),
                "question_id": q["id"],
                "follow_up_depth": 0,
                "role": "interviewer",
                "message": q["question_text"],
            })
            # Candidate answers
            answer = mock_answers[q_idx] if q_idx < len(mock_answers) else "这是我的回答。"
            session.interview_transcript.append({
                "round": len(session.interview_transcript),
                "question_id": q["id"],
                "follow_up_depth": 0,
                "role": "candidate",
                "message": answer,
            })
            # Add a follow-up for most questions
            if q_idx < len(questions_list) - 1:
                session.interview_transcript.append({
                    "round": len(session.interview_transcript),
                    "question_id": q["id"],
                    "follow_up_depth": 1,
                    "role": "interviewer",
                    "message": "能否再具体说说你的思考过程？",
                })
                session.interview_transcript.append({
                    "round": len(session.interview_transcript),
                    "question_id": q["id"],
                    "follow_up_depth": 1,
                    "role": "candidate",
                    "message": "我的思考过程是这样的...",
                })

        session.phase = SessionPhase.INTERVIEW_COMPLETE

        # Phase 4: Evaluation
        eval_svc = get_evaluator_service()
        session.evaluation_result = await eval_svc.evaluate(
            job_profile=session.job_profile,
            question_set=session.question_set,
            transcript=session.interview_transcript,
        )
        session.phase = SessionPhase.EVALUATED

        # Phase 5: Coaching
        coach_svc = get_coach_service()
        session.coaching_result = await coach_svc.generate_coaching(
            evaluation_result=session.evaluation_result,
            transcript=session.interview_transcript,
            job_profile=session.job_profile,
        )
        session.phase = SessionPhase.COACHED

        # Phase 6: Judge
        judge_svc = get_judge_service()
        session.judge_result = await judge_svc.review(
            evaluation_result=session.evaluation_result,
            coaching_result=session.coaching_result,
            transcript=session.interview_transcript,
        )
        session.phase = SessionPhase.JUDGED

        # Phase 7: Report
        report = ReportResponse(
            session_id=session_id,
            phase=session.phase,
            report_markdown="",
            job_profile=session.job_profile,
            evaluation_result=session.evaluation_result,
            coaching_result=session.coaching_result,
            judge_result=session.judge_result,
        )
        session.phase = SessionPhase.COMPLETED

        return FullPipelineResponse(
            session_id=session_id,
            phase=session.phase,
            report=report,
        )

    except Exception as e:
        return FullPipelineResponse(
            session_id=session_id,
            phase="error",
            error=str(e),
        )


# ── Tracing ─────────────────────────────────────────────────────────

@app.get("/api/sessions/{session_id}/traces")
async def get_session_traces(session_id: str):
    return {"session_id": session_id, "traces": get_traces(session_id)}


# ── Eval Metrics (stub) ─────────────────────────────────────────────

@app.get("/api/eval/metrics")
async def get_eval_metrics():
    from backend.llm_client import _mock_jd_parser_response
    return {
        "metrics": {
            "jd_parse_f1": 0.82,
            "question_relevance_mean": 4.1,
            "eval_mae": 0.48,
            "coach_usability": 0.74,
            "judge_detection": 0.85,
        },
        "details": [],
        "badcases": [],
        "aiVsHuman": [],
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
