import { useState, useEffect } from 'react'
import { getEvalMetrics } from '../services/api'
import Loading from '../components/Loading'
import ErrorBanner from '../components/ErrorBanner'

export default function EvalDashboard() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [data, setData] = useState<any>(null)
  const [badcaseFilter, setBadcaseFilter] = useState('all')

  useEffect(() => { loadData() }, [])

  const loadData = async () => {
    try {
      setLoading(true)
      const res = await getEvalMetrics()
      setData(res)
    } catch (e: any) {
      setError(e.message || '加载评测数据失败')
    } finally {
      setLoading(false)
    }
  }

  if (loading) return <Loading text="加载评测数据…" />
  if (error) return <ErrorBanner message={error} onRetry={loadData} />
  if (!data) return <ErrorBanner message="未找到评测数据" />

  const { metrics, details, badcases, aiVsHuman } = data

  const filteredBadcases = badcaseFilter === 'all'
    ? badcases
    : badcases.filter((b: any) => b.severity === badcaseFilter || b.agent === badcaseFilter || b.status === badcaseFilter)

  const statusCount = (status: string) => badcases.filter((b: any) => b.status === status).length
  const severityCount = (sev: string) => badcases.filter((b: any) => b.severity === sev).length

  return (
    <div>
      <div className="page-header">
        <h1>评测面板</h1>
        <p>Agent 评测集结果、AI vs 人工偏差、Badcase 管理</p>
      </div>

      {/* KPI Cards */}
      <div className="grid-4" style={{ marginBottom: 32 }}>
        <div className="card" style={{ textAlign: 'center', padding: '20px 16px' }}>
          <div className="text-xs text-muted" style={{ marginBottom: 4 }}>JD 解析 F1</div>
          <div style={{ fontSize: '2rem', fontWeight: 700, color: metrics.jd_parse_f1 >= 0.80 ? 'var(--color-success)' : 'var(--color-warning)' }}>
            {(metrics.jd_parse_f1 * 100).toFixed(0)}%
          </div>
          <div className="text-xs text-muted">目标 ≥ 80%</div>
        </div>
        <div className="card" style={{ textAlign: 'center', padding: '20px 16px' }}>
          <div className="text-xs text-muted" style={{ marginBottom: 4 }}>题目相关性</div>
          <div style={{ fontSize: '2rem', fontWeight: 700, color: metrics.question_relevance_mean >= 3.8 ? 'var(--color-success)' : 'var(--color-warning)' }}>
            {metrics.question_relevance_mean.toFixed(1)}
          </div>
          <div className="text-xs text-muted">目标 ≥ 3.8 / 5</div>
        </div>
        <div className="card" style={{ textAlign: 'center', padding: '20px 16px' }}>
          <div className="text-xs text-muted" style={{ marginBottom: 4 }}>评估 MAE</div>
          <div style={{ fontSize: '2rem', fontWeight: 700, color: metrics.eval_mae <= 0.50 ? 'var(--color-success)' : 'var(--color-warning)' }}>
            {metrics.eval_mae.toFixed(2)}
          </div>
          <div className="text-xs text-muted">目标 ≤ 0.50</div>
        </div>
        <div className="card" style={{ textAlign: 'center', padding: '20px 16px' }}>
          <div className="text-xs text-muted" style={{ marginBottom: 4 }}>建议可用率</div>
          <div style={{ fontSize: '2rem', fontWeight: 700, color: metrics.coach_usability >= 0.70 ? 'var(--color-success)' : 'var(--color-warning)' }}>
            {(metrics.coach_usability * 100).toFixed(0)}%
          </div>
          <div className="text-xs text-muted">目标 ≥ 70%</div>
        </div>
      </div>

      {/* Metrics Detail Table */}
      <div className="card" style={{ marginBottom: 32 }}>
        <h3 style={{ marginBottom: 16 }}>各 Agent 评测指标详情</h3>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--color-border)' }}>
                <th style={{ textAlign: 'left', padding: '8px 12px', color: 'var(--color-text-secondary)', fontWeight: 500 }}>Agent</th>
                <th style={{ textAlign: 'left', padding: '8px 12px', color: 'var(--color-text-secondary)', fontWeight: 500 }}>指标</th>
                <th style={{ textAlign: 'right', padding: '8px 12px', color: 'var(--color-text-secondary)', fontWeight: 500 }}>实际值</th>
                <th style={{ textAlign: 'right', padding: '8px 12px', color: 'var(--color-text-secondary)', fontWeight: 500 }}>目标值</th>
                <th style={{ textAlign: 'center', padding: '8px 12px', color: 'var(--color-text-secondary)', fontWeight: 500 }}>状态</th>
              </tr>
            </thead>
            <tbody>
              {details.map((row: any) => (
                <tr key={row.id} style={{ borderBottom: '1px solid var(--color-border-light)' }}>
                  <td style={{ padding: '8px 12px', fontWeight: 500 }}>{row.agent}</td>
                  <td style={{ padding: '8px 12px', color: 'var(--color-text-secondary)' }}>{row.metric}</td>
                  <td style={{ padding: '8px 12px', textAlign: 'right', fontFamily: 'var(--font-mono)' }}>{row.value}</td>
                  <td style={{ padding: '8px 12px', textAlign: 'right', fontFamily: 'var(--font-mono)', color: 'var(--color-text-muted)' }}>{row.target}</td>
                  <td style={{ padding: '8px 12px', textAlign: 'center' }}>
                    <span className={`tag ${row.status === 'pass' ? 'tag-green' : 'tag-yellow'}`}>
                      {row.status === 'pass' ? '达标' : '偏弱'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* AI vs Human */}
      <div className="card" style={{ marginBottom: 32 }}>
        <h3 style={{ marginBottom: 16 }}>AI 评分 vs 人工评分偏差分析</h3>
        <p className="text-sm text-secondary" style={{ marginBottom: 16 }}>
          同段对话由 3 位 AI PM 从业者独立评分取均值，与 AI 评估官对比。
          MAE = {metrics.eval_mae.toFixed(2)}，Judge 检出率 = {(metrics.judge_detection * 100).toFixed(0)}%
        </p>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--color-border)' }}>
                <th style={{ textAlign: 'left', padding: '6px 10px', color: 'var(--color-text-secondary)', fontWeight: 500 }}>题目</th>
                <th style={{ textAlign: 'left', padding: '6px 10px', color: 'var(--color-text-secondary)', fontWeight: 500 }}>维度</th>
                <th style={{ textAlign: 'right', padding: '6px 10px', color: 'var(--color-text-secondary)', fontWeight: 500 }}>AI</th>
                <th style={{ textAlign: 'right', padding: '6px 10px', color: 'var(--color-text-secondary)', fontWeight: 500 }}>人工均值</th>
                <th style={{ textAlign: 'right', padding: '6px 10px', color: 'var(--color-text-secondary)', fontWeight: 500 }}>偏差</th>
              </tr>
            </thead>
            <tbody>
              {aiVsHuman.map((row: any, i: number) => (
                <tr key={i} style={{ borderBottom: '1px solid var(--color-border-light)' }}>
                  <td style={{ padding: '6px 10px' }}>Q{row.question_id}</td>
                  <td style={{ padding: '6px 10px', color: 'var(--color-text-secondary)' }}>{row.dimension}</td>
                  <td style={{ padding: '6px 10px', textAlign: 'right', fontFamily: 'var(--font-mono)' }}>{row.ai_score}</td>
                  <td style={{ padding: '6px 10px', textAlign: 'right', fontFamily: 'var(--font-mono)' }}>{row.human_avg.toFixed(1)}</td>
                  <td style={{
                    padding: '6px 10px', textAlign: 'right', fontFamily: 'var(--font-mono)',
                    color: Math.abs(row.delta) > 0.3 ? 'var(--color-danger)' : 'var(--color-text-secondary)',
                  }}>
                    {row.delta > 0 ? '+' : ''}{row.delta.toFixed(1)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Badcase Dashboard */}
      <div className="card">
        <div className="card-header">
          <h3>Badcase 管理</h3>
          <div style={{ display: 'flex', gap: 8 }}>
            <select className="form-select" style={{ fontSize: '0.8rem' }} value={badcaseFilter} onChange={e => setBadcaseFilter(e.target.value)}>
              <option value="all">全部 ({badcases.length})</option>
              <option value="P0">P0 ({severityCount('P0')})</option>
              <option value="P1">P1 ({severityCount('P1')})</option>
              <option value="P2">P2 ({severityCount('P2')})</option>
              <option value="已修复">已修复 ({statusCount('已修复')})</option>
              <option value="修复中">修复中 ({statusCount('修复中')})</option>
            </select>
          </div>
        </div>

        {/* Summary */}
        <div className="grid-3" style={{ marginBottom: 16 }}>
          <div style={{ textAlign: 'center', padding: '12px', background: '#fef2f2', borderRadius: 'var(--radius-sm)' }}>
            <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--color-danger)' }}>{severityCount('P0')}</div>
            <div className="text-xs text-muted">P0 严重</div>
          </div>
          <div style={{ textAlign: 'center', padding: '12px', background: '#fffbeb', borderRadius: 'var(--radius-sm)' }}>
            <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--color-warning)' }}>{severityCount('P1')}</div>
            <div className="text-xs text-muted">P1 重要</div>
          </div>
          <div style={{ textAlign: 'center', padding: '12px', background: '#f8fafc', borderRadius: 'var(--radius-sm)' }}>
            <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--color-success)' }}>{statusCount('已修复')}</div>
            <div className="text-xs text-muted">已修复</div>
          </div>
        </div>

        {/* Badcase List */}
        {filteredBadcases.map((bc: any) => (
          <div key={bc.id} style={{
            padding: '12px 16px', marginBottom: 8,
            background: 'var(--color-border-light)', borderRadius: 'var(--radius-sm)',
            borderLeft: `3px solid ${bc.severity === 'P0' ? 'var(--color-danger)' :
                                     bc.severity === 'P1' ? 'var(--color-warning)' : 'var(--color-text-muted)'}`,
          }}>
            <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 6, flexWrap: 'wrap' }}>
              <span className={`tag ${bc.severity === 'P0' ? 'tag-red' : bc.severity === 'P1' ? 'tag-yellow' : 'tag-green'}`}>
                {bc.severity}
              </span>
              <span className="tag tag-blue">{bc.agent}</span>
              <span className="tag">{bc.type}</span>
              <span className={`tag ${bc.status === '已修复' ? 'tag-green' : 'tag-yellow'}`}>
                {bc.status}
              </span>
            </div>
            <div style={{ fontWeight: 500, marginBottom: 4 }}>{bc.description}</div>
            <div className="grid-2">
              <div>
                <span className="text-xs text-muted">根因：</span>
                <span className="text-sm">{bc.root_cause}</span>
              </div>
              <div>
                <span className="text-xs text-muted">修复：</span>
                <span className="text-sm">{bc.fix}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
