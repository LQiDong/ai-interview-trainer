// ── API Service ────────────────────────────────────────────────────
// Supports both mock mode (default) and real backend calls.

import {
  mockJobProfile, mockQuestions, mockEvaluation,
  mockCoaching, mockJudge, mockEvalMetrics,
  mockEvalDetails, mockBadcases, mockAiVsHuman,
} from '../mock/data'

// Toggle this to switch between mock and real backend
const USE_MOCK = false
const API_BASE: string = import.meta.env.VITE_API_BASE_URL || '/api'

// ── Types ──────────────────────────────────────────────────────────

export interface ApiResponse<T> {
  data: T | null
  error: string | null
  loading: boolean
}

// ── Helpers ────────────────────────────────────────────────────────

function delay(ms: number = 600): Promise<void> {
  return new Promise(r => setTimeout(r, ms))
}

async function apiGet<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`)
  if (!res.ok) {
    const body = await res.text()
    throw new Error(`API ${res.status}: ${body}`)
  }
  return res.json()
}

async function apiPost<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined,
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`API ${res.status}: ${text}`)
  }
  return res.json()
}

// ── Session ────────────────────────────────────────────────────────

export async function createSession(): Promise<string> {
  if (USE_MOCK) {
    await delay(300)
    return 'mock-' + Math.random().toString(36).slice(2, 10)
  }
  const data: any = await apiPost('/sessions')
  return data.session_id
}

// ── JD Parser ──────────────────────────────────────────────────────

export async function parseJD(sessionId: string, jdText: string, targetPosition: string = ''): Promise<any> {
  if (USE_MOCK) {
    await delay(800)
    return { session_id: sessionId, phase: 'jd_parsed', job_profile: mockJobProfile }
  }
  return apiPost(`/sessions/${sessionId}/parse-jd`, { jd_text: jdText, target_position: targetPosition })
}

// ── Questions ──────────────────────────────────────────────────────

export async function generateQuestions(sessionId: string): Promise<any> {
  if (USE_MOCK) {
    await delay(500)
    return { session_id: sessionId, phase: 'questions_ready', question_set: mockQuestions }
  }
  return apiPost(`/sessions/${sessionId}/questions`)
}

// ── Interview ──────────────────────────────────────────────────────

export async function startInterview(sessionId: string): Promise<any> {
  if (USE_MOCK) {
    await delay(400)
    return {
      session_id: sessionId, phase: 'interviewing',
      action: 'ask_question', question_id: 1, question_number: 1,
      total_questions: 7, follow_up_depth: 0,
      message: mockQuestions.questions[0].question_text,
    }
  }
  return apiPost(`/sessions/${sessionId}/start`)
}

export async function submitAnswer(sessionId: string, answer: string): Promise<any> {
  if (USE_MOCK) {
    await delay(700)
    // Simulate mock interviewer behavior
    const stored = sessionStorage.getItem(`interview_${sessionId}`)
    let state = stored ? JSON.parse(stored) : { qIdx: 0, fuDepth: 0, rounds: 0 }
    state.rounds++

    const followUps = [
      ['能否具体说说你在其中的具体角色和关键决策？', '你提到了技术挑战，能展开说说具体是什么问题吗？', '这个成果中你的个人贡献具体体现在哪里？'],
      ['如果重来一次，你会做什么不同的决策？', '有没有考虑过替代方案？你为什么选择了当前这个？', '你是如何衡量这个解决方案的效果的？'],
      ['能举一个具体的Agent协作场景说明其中的难点吗？', 'Agent之间的通信协议你是怎么设计的？', '工具调用的可靠性你是怎么保证的？'],
      ['这个数据结论有没有做置信度检验？', '如果数据支持A但直觉支持B，你怎么决策？', '你如何确保数据不会误导你的产品判断？'],
      ['能举一个和工程团队在技术可行性上有分歧的具体案例吗？', '如果工程团队说"做不了"，你会怎么处理？', '你是如何平衡技术理想和业务现实的？'],
      ['你提到可用性，能具体用量化指标定义吗？', '你如何区分"用户不喜欢"和"用户不理解"？', 'AI产品的评估和传统产品有什么不同？'],
      ['你觉得相比其他候选人，你最大的差异化优势是什么？', '对未来3年AI产品的发展有什么判断？'],
    ]

    const questions = mockQuestions.questions
    let response

    if (state.fuDepth < 2 && state.qIdx < followUps.length && state.fuDepth < followUps[state.qIdx].length) {
      response = {
        session_id: sessionId,
        action: 'follow_up',
        question_id: state.qIdx + 1,
        question_number: state.qIdx + 1,
        total_questions: questions.length,
        follow_up_depth: state.fuDepth + 1,
        follow_up_reason: `候选人的回答在第${state.fuDepth + 1}层可进一步深挖`,
        message: followUps[state.qIdx][state.fuDepth],
        interview_complete: false,
      }
      state.fuDepth++
    } else {
      state.qIdx++
      state.fuDepth = 0
      if (state.qIdx >= questions.length) {
        response = {
          session_id: sessionId,
          action: 'end_interview',
          message: '好的，我们的面试到这里就结束了。接下来系统将为你生成详细的评估报告。',
          interview_complete: true,
        }
      } else {
        response = {
          session_id: sessionId,
          action: 'ask_question',
          question_id: state.qIdx + 1,
          question_number: state.qIdx + 1,
          total_questions: questions.length,
          follow_up_depth: 0,
          message: questions[state.qIdx].question_text,
          interview_complete: false,
        }
      }
    }

    sessionStorage.setItem(`interview_${sessionId}`, JSON.stringify(state))
    return response
  }
  return apiPost(`/sessions/${sessionId}/answer`, { answer })
}

// ── Evaluation ─────────────────────────────────────────────────────

export async function requestEvaluation(sessionId: string): Promise<any> {
  if (USE_MOCK) {
    await delay(1200)
    return { session_id: sessionId, phase: 'evaluated', evaluation_result: mockEvaluation }
  }
  return apiPost(`/sessions/${sessionId}/evaluate`)
}

// ── Coaching ───────────────────────────────────────────────────────

export async function requestCoaching(sessionId: string): Promise<any> {
  if (USE_MOCK) {
    await delay(900)
    return { session_id: sessionId, phase: 'coached', coaching_result: mockCoaching }
  }
  return apiPost(`/sessions/${sessionId}/coach`)
}

// ── Judge ──────────────────────────────────────────────────────────

export async function requestJudge(sessionId: string): Promise<any> {
  if (USE_MOCK) {
    await delay(700)
    return { session_id: sessionId, phase: 'judged', judge_result: mockJudge }
  }
  return apiPost(`/sessions/${sessionId}/judge`)
}

// ── Report ─────────────────────────────────────────────────────────

export async function getReport(sessionId: string): Promise<any> {
  if (USE_MOCK) {
    await delay(500)
    return {
      session_id: sessionId,
      phase: 'completed',
      report_markdown: '',
      job_profile: mockJobProfile,
      evaluation_result: mockEvaluation,
      coaching_result: mockCoaching,
      judge_result: mockJudge,
      disclaimer: '本报告由 AI 系统自动生成，仅供面试准备参考，不构成任何形式的面试通过率承诺或保证。',
    }
  }
  return apiGet(`/sessions/${sessionId}/report`)
}

// ── Eval Dashboard ─────────────────────────────────────────────────

export async function getEvalMetrics(): Promise<any> {
  if (USE_MOCK) {
    await delay(400)
    return { metrics: mockEvalMetrics, details: mockEvalDetails, badcases: mockBadcases, aiVsHuman: mockAiVsHuman }
  }
  return apiGet('/eval/metrics')
}
