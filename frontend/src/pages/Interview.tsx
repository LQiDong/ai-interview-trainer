import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { startInterview, submitAnswer, requestEvaluation, requestCoaching, requestJudge } from '../services/api'
import Loading from '../components/Loading'
import ErrorBanner from '../components/ErrorBanner'
import ScoreBadge from '../components/ScoreBadge'

interface Message {
  role: 'interviewer' | 'candidate' | 'system'
  text: string
  metadata?: string
}

type Phase = 'connecting' | 'interviewing' | 'evaluating' | 'done' | 'error'

export default function Interview() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const navigate = useNavigate()
  const chatEndRef = useRef<HTMLDivElement>(null)

  const [phase, setPhase] = useState<Phase>('connecting')
  const [messages, setMessages] = useState<Message[]>([])
  const [answer, setAnswer] = useState('')
  const [error, setError] = useState('')
  const [status, setStatus] = useState({ question: 0, total: 7, round: 0, fuDepth: 0 })
  const [isSubmitting, setIsSubmitting] = useState(false)

  // Init
  useEffect(() => {
    if (!sessionId) {
      navigate('/jd-input')
      return
    }
    initInterview()
  }, [sessionId])

  const initInterview = async () => {
    try {
      setPhase('connecting')
      const res = await startInterview(sessionId!)
      setMessages([{ role: 'interviewer', text: res.message }])
      setStatus(s => ({ ...s, question: res.question_number || 1, total: res.total_questions || 7 }))
      setPhase('interviewing')
    } catch (e: any) {
      setError(e.message || '初始化面试失败')
      setPhase('error')
    }
  }

  // Auto scroll
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSubmit = async () => {
    if (!answer.trim() || isSubmitting) return

    const candidateMsg: Message = { role: 'candidate', text: answer }
    setMessages(prev => [...prev, candidateMsg])
    setAnswer('')
    setIsSubmitting(true)

    try {
      const res = await submitAnswer(sessionId!, answer)

      if (res.interview_complete) {
        setMessages(prev => [...prev, { role: 'system', text: res.message }])
        setPhase('evaluating')
        await runEvaluation()
      } else {
        const metadata = res.action === 'follow_up'
          ? `追问 · Q${res.question_id} · 第${res.follow_up_depth}层`
          : `Q${res.question_number}/${res.total_questions}`
        setMessages(prev => [...prev, {
          role: 'interviewer',
          text: res.message,
          metadata,
        }])
        setStatus(s => ({
          ...s,
          question: res.question_number || s.question,
          total: res.total_questions || s.total,
          round: s.round + 1,
          fuDepth: res.follow_up_depth || 0,
        }))
      }
    } catch (e: any) {
      setError(e.message || '提交失败')
    } finally {
      setIsSubmitting(false)
    }
  }

  const runEvaluation = async () => {
    try {
      setMessages(prev => [...prev, { role: 'system', text: '⏳ 评估官 Agent 正在评分…' }])
      await requestEvaluation(sessionId!)

      setMessages(prev => [...prev, { role: 'system', text: '⏳ 教练 Agent 正在生成建议…' }])
      await requestCoaching(sessionId!)

      setMessages(prev => [...prev, { role: 'system', text: '⏳ Judge Agent 正在复核…' }])
      await requestJudge(sessionId!)

      setPhase('done')
      setMessages(prev => [...prev, {
        role: 'system',
        text: '✅ 评估完成！正在跳转到诊断报告…',
      }])

      setTimeout(() => {
        navigate(`/report/${sessionId}`)
      }, 1200)
    } catch (e: any) {
      setError(e.message || '评估失败')
      setPhase('error')
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  return (
    <div>
      <div className="page-header">
        <h1>模拟面试</h1>
        <p>AI 面试官会根据你的回答动态追问，请尽量详细作答</p>
      </div>

      {/* Status Bar */}
      <div className="status-bar">
        <div className="status-item">
          <span className={`status-dot ${phase === 'interviewing' ? 'active' : 'idle'}`} />
          <span>{phase === 'interviewing' ? '面试中' : phase === 'evaluating' ? '评估中' : phase === 'done' ? '已完成' : '连接中'}</span>
        </div>
        <div className="status-item text-muted">|</div>
        <div className="status-item">
          题目 <strong>{status.question}/{status.total}</strong>
        </div>
        <div className="status-item text-muted">|</div>
        <div className="status-item">
          对话轮次 <strong>{status.round}</strong>
        </div>
        {status.fuDepth > 0 && (
          <>
            <div className="status-item text-muted">|</div>
            <div className="status-item">
              追问深度 <strong>{status.fuDepth}</strong>
            </div>
          </>
        )}
      </div>

      {error && (
        <div style={{ marginBottom: 16 }}>
          <ErrorBanner message={error} onRetry={initInterview} />
        </div>
      )}

      {/* Chat Area */}
      <div
        className="card"
        style={{
          padding: '20px',
          marginBottom: 16,
          maxHeight: '50vh',
          overflowY: 'auto',
          background: '#fafbfc',
        }}
      >
        {messages.length === 0 && phase === 'connecting' && (
          <Loading text="初始化面试…" />
        )}

        {messages.map((msg, i) => (
          <div
            key={i}
            style={{
              marginBottom: 16,
              display: 'flex',
              flexDirection: 'column',
              alignItems: msg.role === 'candidate' ? 'flex-end' : 'flex-start',
            }}
          >
            {msg.metadata && (
              <div className="text-xs text-muted" style={{ marginBottom: 4 }}>
                {msg.metadata}
              </div>
            )}
            <div
              style={{
                maxWidth: '85%',
                padding: '10px 16px',
                borderRadius: msg.role === 'candidate' ? '12px 12px 4px 12px' :
                             msg.role === 'system' ? '8px' : '12px 12px 12px 4px',
                background: msg.role === 'candidate'
                  ? 'var(--color-primary)'
                  : msg.role === 'system'
                  ? 'var(--color-border-light)'
                  : '#fff',
                color: msg.role === 'candidate' ? '#fff' : 'var(--color-text)',
                border: msg.role === 'interviewer' ? '1px solid var(--color-border)' : 'none',
                fontSize: '0.9rem',
                lineHeight: 1.65,
                whiteSpace: 'pre-wrap',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 2 }}>
                <span style={{ fontSize: '0.8rem', fontWeight: 600, opacity: 0.8 }}>
                  {msg.role === 'interviewer' ? '🤖 面试官' :
                   msg.role === 'candidate' ? '👤 你' :
                   '📋 系统'}
                </span>
              </div>
              {msg.text}
            </div>
          </div>
        ))}
        <div ref={chatEndRef} />
      </div>

      {/* Input Area */}
      {phase === 'interviewing' && (
        <div className="card" style={{ padding: '16px 20px' }}>
          <div style={{ display: 'flex', gap: 12, alignItems: 'flex-end' }}>
            <textarea
              className="form-textarea"
              rows={3}
              placeholder="输入你的回答…（Enter 发送，Shift+Enter 换行）"
              value={answer}
              onChange={e => setAnswer(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={isSubmitting}
              style={{ flex: 1, resize: 'none' }}
              autoFocus
            />
            <button
              className="btn btn-primary"
              onClick={handleSubmit}
              disabled={!answer.trim() || isSubmitting}
              style={{ height: 'fit-content', padding: '12px 24px' }}
            >
              {isSubmitting ? '发送中…' : '发送 ↵'}
            </button>
          </div>
          <div className="text-xs text-muted mt-8">
            按 Enter 发送，Shift+Enter 换行 · 输入 "/end" 可提前结束面试
          </div>
        </div>
      )}

      {phase === 'evaluating' && (
        <div className="card" style={{ textAlign: 'center', padding: 32 }}>
          <Loading text="正在评估面试表现…" />
          <div className="text-sm text-secondary mt-16">
            评估官 → 教练 → Judge 三位 Agent 依次工作中
          </div>
        </div>
      )}

      {phase === 'done' && (
        <div className="card" style={{ textAlign: 'center', padding: 32 }}>
          <div style={{ fontSize: '2rem', marginBottom: 8 }}>✅</div>
          <h3>面试完成</h3>
          <p className="text-secondary mt-8">正在跳转到诊断报告…</p>
        </div>
      )}
    </div>
  )
}
