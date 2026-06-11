import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getReport } from '../services/api'
import RadarChart from '../components/RadarChart'
import ScoreBadge from '../components/ScoreBadge'
import Loading from '../components/Loading'
import ErrorBanner from '../components/ErrorBanner'

const DIM_LABELS: Record<string, string> = {
  content_relevance: '内容匹配度',
  structure_clarity: '结构清晰度',
  evidence_support: '证据支撑度',
  expression_credibility: '表达可信度',
}
const DIM_WEIGHTS: Record<string, number> = {
  content_relevance: 0.35,
  structure_clarity: 0.25,
  evidence_support: 0.25,
  expression_credibility: 0.15,
}

export default function Report() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [data, setData] = useState<any>(null)
  const [activeTab, setActiveTab] = useState<'overview' | 'questions' | 'coaching' | 'judge'>('overview')

  useEffect(() => {
    if (!sessionId) { navigate('/jd-input'); return }
    loadReport()
  }, [sessionId])

  const loadReport = async () => {
    try {
      setLoading(true)
      const res = await getReport(sessionId!)
      setData(res)
    } catch (e: any) {
      setError(e.message || '加载报告失败')
    } finally {
      setLoading(false)
    }
  }

  if (loading) return <Loading text="加载诊断报告…" />
  if (error) return <ErrorBanner message={error} onRetry={loadReport} />
  if (!data) return <ErrorBanner message="未找到报告数据" />

  const eval_ = data.evaluation_result
  const dims = eval_?.dimension_summary || {}
  const overall = eval_?.overall_assessment || {}
  const coaching = data.coaching_result
  const judge = data.judge_result

  // Radar data
  const radarData = Object.entries(dims).map(([key, val]: [string, any]) => ({
    label: DIM_LABELS[key] || key,
    score: val.average_score || 0,
    maxScore: val.max_score || 3,
  }))

  const tabs = [
    { key: 'overview' as const, label: '总览' },
    { key: 'questions' as const, label: '逐题分析' },
    { key: 'coaching' as const, label: '教练建议' },
    { key: 'judge' as const, label: 'Judge 复核' },
  ]

  return (
    <div>
      <div className="page-header">
        <h1>面试诊断报告</h1>
        <p>
          岗位：{data.job_profile?.position?.title || '未知'} · {data.job_profile?.position?.level || ''}
          {' · '}总分 {overall.weighted_total_score?.toFixed(2)}/{overall.max_score || 3}
        </p>
      </div>

      {/* Disclaimer */}
      <div style={{
        background: '#fffbeb', border: '1px solid #fcd34d', borderRadius: 'var(--radius-sm)',
        padding: '10px 14px', fontSize: '0.8rem', color: '#92400e', marginBottom: 24,
      }}>
        ⚠️ {data.disclaimer}
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 4, marginBottom: 24, borderBottom: '1px solid var(--color-border)', paddingBottom: 0 }}>
        {tabs.map(t => (
          <button
            key={t.key}
            className={`btn btn-sm ${activeTab === t.key ? 'btn-primary' : 'btn-secondary'}`}
            style={{ borderRadius: '6px 6px 0 0', borderBottom: 'none' }}
            onClick={() => setActiveTab(t.key)}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* ── Overview Tab ───────────────────────────────────────── */}
      {activeTab === 'overview' && (
        <>
          {/* Score summary */}
          <div className="grid-2" style={{ marginBottom: 24 }}>
            <div className="card" style={{ textAlign: 'center' }}>
              <h3 style={{ marginBottom: 16 }}>四维雷达图</h3>
              <RadarChart data={radarData} size={280} />
              <div className="text-xs text-muted mt-8">
                加权总分 = 内容匹配度×0.35 + 结构清晰度×0.25 + 证据支撑度×0.25 + 表达可信度×0.15
              </div>
            </div>
            <div className="card">
              <h3 style={{ marginBottom: 16 }}>维度得分</h3>
              {Object.entries(dims).map(([key, val]: [string, any]) => (
                <div key={key} style={{ marginBottom: 14 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                    <span style={{ fontWeight: 500, fontSize: '0.9rem' }}>
                      {DIM_LABELS[key] || key}
                    </span>
                    <ScoreBadge score={val.average_score} maxScore={val.max_score || 3} size="sm" />
                  </div>
                  <div style={{
                    height: 6, background: 'var(--color-border-light)', borderRadius: 3, overflow: 'hidden',
                  }}>
                    <div style={{
                      height: '100%',
                      width: `${((val.average_score || 0) / (val.max_score || 3)) * 100}%`,
                      background: `var(--color-${val.average_score >= 2 ? 'success' : val.average_score >= 1 ? 'warning' : 'danger'})`,
                      borderRadius: 3,
                      transition: 'width 0.5s ease',
                    }} />
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 4, fontSize: '0.75rem' }}>
                    <span className="text-success">✓ {val.top_strength}</span>
                    <span className="text-danger">✗ {val.top_weakness}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Overall */}
          <div className="card">
            <div className="card-header">
              <h3>综合评估</h3>
              <span className={`tag ${overall.weighted_total_score >= 2 ? 'tag-green' : overall.weighted_total_score >= 1.2 ? 'tag-yellow' : 'tag-red'}`}>
                {overall.interview_performance_level || '未知'}
              </span>
            </div>
            <p style={{ lineHeight: 1.8 }}>{overall.summary}</p>
          </div>
        </>
      )}

      {/* ── Questions Tab ──────────────────────────────────────── */}
      {activeTab === 'questions' && (
        <div>
          {eval_?.per_question_scores?.map((q: any) => (
            <div key={q.question_id} className="card" style={{ marginBottom: 16 }}>
              <div className="card-header">
                <div>
                  <span className="text-xs text-muted">Q{q.question_id}</span>
                  <h3 style={{ margin: '4px 0 0' }}>{q.question_text}</h3>
                </div>
                <ScoreBadge
                  score={
                    Object.values(DIM_LABELS).reduce((sum: number, _: string, _i: number, arr: string[]) => {
                      const keys = Object.keys(DIM_LABELS)
                      return sum + (q[keys[_i]]?.score || 0)
                    }, 0) / 4
                  }
                  maxScore={3}
                  label="均分"
                />
              </div>

              <div className="grid-2">
                {Object.entries(DIM_LABELS).map(([key, label]) => {
                  const dimData = q[key]
                  if (!dimData) return null
                  return (
                    <div key={key} style={{
                      padding: '10px 14px',
                      background: 'var(--color-border-light)',
                      borderRadius: 'var(--radius-sm)',
                    }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                        <span style={{ fontWeight: 600, fontSize: '0.85rem' }}>{label}</span>
                        <ScoreBadge score={dimData.score} maxScore={3} size="sm" />
                      </div>
                      <div className="text-xs text-secondary" style={{ marginBottom: 6 }}>
                        {dimData.evidence}
                      </div>
                      {dimData.deduction_points?.length > 0 && (
                        <div>
                          {dimData.deduction_points.map((dp: string, i: number) => (
                            <div key={i} className="text-xs text-danger" style={{ marginTop: 2 }}>
                              ✗ {dp}
                            </div>
                          ))}
                        </div>
                      )}
                      {dimData.hit_points?.length > 0 && (
                        <div>
                          {dimData.hit_points.map((hp: string, i: number) => (
                            <div key={i} className="text-xs text-success" style={{ marginTop: 2 }}>
                              ✓ {hp}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* ── Coaching Tab ───────────────────────────────────────── */}
      {activeTab === 'coaching' && coaching && (
        <div>
          {/* Priority */}
          <div className="card" style={{ marginBottom: 16, background: '#eff6ff', borderColor: '#bfdbfe' }}>
            <div className="card-header">
              <h3>🎯 最优先改进维度</h3>
              <span className="tag tag-red">{DIM_LABELS[coaching.coaching_meta?.improvement_priority] || coaching.coaching_meta?.improvement_priority}</span>
            </div>
            <p className="text-sm">{coaching.coaching_meta?.priority_rationale}</p>
          </div>

          {/* Top 3 Actions */}
          <h3 style={{ marginBottom: 12 }}>Top 3 优先行动项</h3>
          {coaching.top_3_actions?.map((action: any) => (
            <div key={action.rank} className="card" style={{ marginBottom: 12 }}>
              <div className="card-header">
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span style={{
                    background: 'var(--color-primary)', color: '#fff',
                    borderRadius: '50%', width: 28, height: 28,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: '0.8rem', fontWeight: 700,
                  }}>
                    {action.rank}
                  </span>
                  <h3 style={{ fontSize: '0.95rem' }}>{action.action}</h3>
                </div>
                <span className="tag tag-blue">{DIM_LABELS[action.target_dimension] || action.target_dimension}</span>
              </div>
              <div className="grid-2 mt-16">
                <div>
                  <div className="text-xs text-muted" style={{ marginBottom: 2 }}>预期效果</div>
                  <div className="text-sm">{action.expected_impact}</div>
                </div>
                <div>
                  <div className="text-xs text-muted" style={{ marginBottom: 2 }}>练习方法</div>
                  <div className="text-sm">{action.practice_method}</div>
                </div>
              </div>
              <div className="text-xs text-muted mt-8">预计用时：{action.time_estimate}</div>
            </div>
          ))}

          {/* Per Question Coaching */}
          <h3 style={{ marginBottom: 12, marginTop: 24 }}>逐题教练建议</h3>
          {coaching.per_question_coaching?.map((q: any) => (
            <div key={q.question_id} className="card" style={{ marginBottom: 12 }}>
              <div className="card-header">
                <div>
                  <span className="text-xs text-muted">Q{q.question_id}</span>
                  <h3 style={{ margin: '2px 0 0', fontSize: '0.9rem' }}>{q.question_text}</h3>
                </div>
              </div>
              {q.coaching_entries?.map((entry: any, i: number) => (
                <div key={i} style={{
                  padding: '12px 14px',
                  background: 'var(--color-border-light)',
                  borderRadius: 'var(--radius-sm)',
                  marginBottom: 10,
                }}>
                  <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 6 }}>
                    <span className="tag tag-red">{DIM_LABELS[entry.target_dimension] || entry.target_dimension}</span>
                    <span className="text-xs text-muted">扣分点：{entry.deduction_point_from_evaluator}</span>
                  </div>
                  <div className="text-sm" style={{ marginBottom: 6 }}>
                    <strong>为什么重要：</strong>{entry.why_it_matters}
                  </div>
                  <div className="text-sm" style={{ marginBottom: 8 }}>
                    <strong>如何改进：</strong>{entry.how_to_improve}
                  </div>
                  {entry.example_better_response && (
                    <div style={{
                      background: '#f0fdf4', border: '1px solid #bbf7d0',
                      borderRadius: 'var(--radius-sm)', padding: '10px 14px',
                    }}>
                      <div className="text-xs text-success" style={{ marginBottom: 4, fontWeight: 600 }}>📝 范例回答</div>
                      <div className="text-sm" style={{ lineHeight: 1.7 }}>{entry.example_better_response}</div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          ))}

          {/* General Advice */}
          <div className="card mt-16" style={{ background: '#f8fafc' }}>
            <h3 style={{ marginBottom: 8 }}>📋 总体建议</h3>
            <p style={{ lineHeight: 1.8 }}>{coaching.general_advice}</p>
          </div>
        </div>
      )}

      {/* ── Judge Tab ──────────────────────────────────────────── */}
      {activeTab === 'judge' && judge && (
        <div>
          <div className="card" style={{ marginBottom: 16 }}>
            <div className="card-header">
              <h3>复核结论</h3>
              <span className={`tag ${judge.overall_verdict === 'pass' ? 'tag-green' : judge.overall_verdict === 'pass_with_issues' ? 'tag-yellow' : 'tag-red'}`}>
                {judge.overall_verdict === 'pass' ? '✅ 全部通过' :
                 judge.overall_verdict === 'pass_with_issues' ? '⚠ 通过（有建议）' :
                 '❌ 需要修复'}
              </span>
            </div>
            <p className="text-sm">{judge.verdict_rationale}</p>
          </div>

          {judge.check_results && Object.entries(judge.check_results).map(([checkId, check]: [string, any]) => (
            <div key={checkId} className="card" style={{ marginBottom: 12 }}>
              <div className="card-header">
                <h3 style={{ fontSize: '0.95rem' }}>
                  {checkId === 'score_evidence_consistency' && '检查 1：分数与评语一致性'}
                  {checkId === 'low_score_deduction_completeness' && '检查 2：低分扣分点完整性'}
                  {checkId === 'coach_evaluator_alignment' && '检查 3：教练建议与评估对齐'}
                  {checkId === 'over_promise_detection' && '检查 4：过度承诺检测'}
                </h3>
                <span className={`tag ${check.passed ? 'tag-green' : 'tag-red'}`}>
                  {check.passed ? '通过' : `${check.total_issues} 项问题`}
                </span>
              </div>
              {check.issues?.map((issue: any, i: number) => (
                <div key={i} style={{
                  padding: '10px 14px', marginBottom: 8,
                  background: issue.severity === 'critical' ? '#fef2f2' :
                              issue.severity === 'high' ? '#fffbeb' : '#f8fafc',
                  borderRadius: 'var(--radius-sm)',
                  border: `1px solid ${issue.severity === 'critical' ? '#fecaca' :
                                        issue.severity === 'high' ? '#fcd34d' : 'var(--color-border)'}`,
                }}>
                  <div style={{ display: 'flex', gap: 6, alignItems: 'center', marginBottom: 4 }}>
                    <span className={`tag ${issue.severity === 'critical' ? 'tag-red' :
                                          issue.severity === 'high' ? 'tag-yellow' :
                                          issue.severity === 'medium' ? 'tag-blue' : 'tag-green'}`}>
                      {issue.severity}
                    </span>
                    <span className="text-xs text-muted">{issue.finding}</span>
                  </div>
                  <div className="text-sm">{issue.detail}</div>
                  {issue.recommendation && (
                    <div className="text-sm text-success mt-4">💡 {issue.recommendation}</div>
                  )}
                </div>
              ))}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
