import { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { createSession, parseJD, generateQuestions } from '../services/api'
import Loading from '../components/Loading'
import ErrorBanner from '../components/ErrorBanner'

type Phase = 'input' | 'parsing' | 'generating' | 'done' | 'error'

const SAMPLE_JD = `【岗位】AI产品经理（Agent方向）

【职责】
1. 负责AI Agent平台的产品规划和设计，推动产品从0到1落地
2. 与工程、算法团队紧密协作，定义Agent的能力边界和交互体验
3. 制定产品路线图，跟踪关键指标并持续优化
4. 深入研究Multi-Agent协作机制，将前沿技术转化为产品能力

【要求】
- 3-5年产品经理经验，其中至少1年AI产品经验
- 熟悉Agent架构设计、Prompt Engineering
- 有B端SaaS产品经验优先
- 优秀的跨团队沟通和推动能力`

export default function JDInput() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const [jdText, setJdText] = useState('')
  const [targetPosition, setTargetPosition] = useState(searchParams.get('role') || '')
  const [phase, setPhase] = useState<Phase>('input')
  const [error, setError] = useState('')
  const [jobProfile, setJobProfile] = useState<any>(null)

  const useSample = () => {
    setJdText(SAMPLE_JD)
    setTargetPosition('AI产品经理')
  }

  const handleSubmit = async () => {
    if (!jdText.trim()) {
      setError('请输入 JD 内容')
      return
    }

    setError('')
    setPhase('parsing')

    try {
      const sessionId = await createSession()
      const parseResult = await parseJD(sessionId, jdText, targetPosition)
      setJobProfile(parseResult.job_profile)
      setPhase('generating')

      const qResult = await generateQuestions(sessionId)
      // Store session data for the interview page
      sessionStorage.setItem(`session_${sessionId}`, JSON.stringify({
        sessionId,
        jobProfile: parseResult.job_profile,
        questionSet: qResult.question_set,
      }))
      sessionStorage.setItem('currentSessionId', sessionId)

      setPhase('done')
    } catch (e: any) {
      setError(e.message || '请求失败，请重试')
      setPhase('error')
    }
  }

  const startInterview = () => {
    const sessionId = sessionStorage.getItem('currentSessionId')
    if (sessionId) {
      navigate(`/interview/${sessionId}`)
    }
  }

  return (
    <div>
      <div className="page-header">
        <span className="page-kicker">创建训练</span>
        <h1>用目标岗位，生成你的专属面试</h1>
        <p>选择岗位方向并粘贴 JD。信息越完整，问题和评价标准越贴近真实招聘。</p>
      </div>

      {error && (
        <div style={{ marginBottom: 16 }}>
          <ErrorBanner message={error} onRetry={() => { setError(''); setPhase('input') }} />
        </div>
      )}

      {/* Phase: Input */}
      {(phase === 'input' || phase === 'error') && (
        <div className="card">
          <div className="card-header jd-card-header">
            <div><h3>岗位信息</h3><p>通常 30 秒内完成分析和出题</p></div>
            <button className="btn btn-sm btn-secondary" onClick={useSample}>
              填入示例 JD
            </button>
          </div>

          <div className="form-group">
            <label className="form-label">目标岗位类型（可选）</label>
            <select
              className="form-select"
              value={targetPosition}
              onChange={e => setTargetPosition(e.target.value)}
              style={{ width: '100%', maxWidth: 320 }}
            >
              <option value="">自动判断</option>
              <option value="AI产品经理">AI 产品经理</option>
              <option value="AI产品运营">AI 产品运营</option>
              <option value="Agent产品经理">Agent 产品经理</option>
              <option value="Agent 开发工程师">Agent 开发工程师</option>
              <option value="产品经理">产品经理</option>
              <option value="全栈工程师">全栈工程师</option>
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">
              粘贴 JD 原文
              <span className="text-muted text-sm" style={{ marginLeft: 8 }}>
                （含公司介绍、福利等内容会被自动过滤）
              </span>
            </label>
            <textarea
              className="form-textarea"
              rows={12}
              placeholder="在此粘贴目标岗位的 JD（Job Description）…"
              value={jdText}
              onChange={e => setJdText(e.target.value)}
            />
            <div className="text-xs text-muted mt-8">
              已输入 {jdText.length} 字
            </div>
          </div>

          <button
            className="btn btn-primary btn-lg"
            onClick={handleSubmit}
            disabled={!jdText.trim()}
          >
            生成专属面试题 →
          </button>
        </div>
      )}

      {/* Phase: Parsing / Generating */}
      {(phase === 'parsing' || phase === 'generating') && (
        <div className="card" style={{ textAlign: 'center', padding: 48 }}>
          <Loading text={phase === 'parsing' ? '正在解析 JD，提取岗位画像…' : '正在生成定制化面试题和追问树…'} />
          <div className="text-sm text-secondary mt-16">
            {phase === 'parsing' ? 'JD Parser Agent 工作中' : '出题官 Agent 工作中'}
          </div>
        </div>
      )}

      {/* Phase: Done — show Job Profile preview */}
      {phase === 'done' && jobProfile && (
        <>
          {/* Job Profile Preview */}
          <div className="card mb-16">
            <div className="card-header">
              <h3>✅ 岗位画像解析完成</h3>
              <span className="tag tag-green">置信度：{jobProfile.confidence?.overall === 'high' ? '高' : '中'}</span>
            </div>
            <div className="grid-2">
              <div>
                <div className="text-xs text-muted" style={{ marginBottom: 4 }}>岗位</div>
                <div style={{ fontWeight: 600 }}>{jobProfile.position?.title} · {jobProfile.position?.level}</div>
              </div>
              <div>
                <div className="text-xs text-muted" style={{ marginBottom: 4 }}>分类</div>
                <div style={{ fontWeight: 600 }}>{jobProfile.position?.inferred_category}</div>
              </div>
              <div>
                <div className="text-xs text-muted" style={{ marginBottom: 4 }}>经验要求</div>
                <div style={{ fontWeight: 600 }}>{jobProfile.experience_requirements?.years}</div>
              </div>
              <div>
                <div className="text-xs text-muted" style={{ marginBottom: 4 }}>行业</div>
                <div style={{ fontWeight: 600 }}>{jobProfile.company_context?.industry}</div>
              </div>
            </div>

            <div className="mt-16">
              <div className="text-xs text-muted" style={{ marginBottom: 6 }}>面试重点考察方向</div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                {jobProfile.interview_focus_areas?.map((area: any) => (
                  <span key={area.area} className={`tag ${area.priority === '高' ? 'tag-red' : 'tag-yellow'}`}>
                    {area.area} · {area.priority}
                  </span>
                ))}
              </div>
            </div>

            <div className="mt-16">
              <div className="text-xs text-muted" style={{ marginBottom: 6 }}>核心硬技能</div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                {jobProfile.hard_skills?.map((s: any) => (
                  <span key={s.skill} className={`tag ${s.requirement_level === '必须' ? 'tag-blue' : 'tag-green'}`}>
                    {s.skill} · {s.requirement_level}
                  </span>
                ))}
              </div>
            </div>
          </div>

          {/* Start Interview */}
          <div style={{ textAlign: 'center' }}>
            <button className="btn btn-primary btn-lg" onClick={startInterview}>
              开始模拟面试 →
            </button>
            <p className="text-sm text-secondary mt-8">
              面试共 7 题，预计 15-20 分钟。AI 面试官会根据你的回答动态追问。
            </p>
          </div>
        </>
      )}
    </div>
  )
}
