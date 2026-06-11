import { Link } from 'react-router-dom'

const features = [
  {
    icon: '📋', title: 'JD 驱动出题',
    desc: '粘贴目标岗位 JD，AI 自动解析岗位画像并生成定制化面试题，精准匹配考察方向。',
  },
  {
    icon: '💬', title: '多轮追问面试',
    desc: 'AI 面试官根据你的回答进行 3-5 层递进追问，模拟真实面试的压力场景。',
  },
  {
    icon: '📊', title: '四维结构化评估',
    desc: '内容匹配度、结构清晰度、证据支撑度、表达可信度 —— 四个维度独立打分，有据可查。',
  },
  {
    icon: '🎯', title: '可行动的教练建议',
    desc: '每条改进建议对应一个具体扣分点。不告诉你"答得不好"，而是告诉你"下次怎么答更好"。',
  },
  {
    icon: '🛡️', title: 'Judge 质量复核',
    desc: '独立复核 Agent 检查评分一致性、建议有效性、以及是否存在过度承诺。',
  },
  {
    icon: '📈', title: '评测驱动迭代',
    desc: '构建评测集 + Badcase 管理系统，用数据驱动 Agent 质量提升，而非拍脑袋调 Prompt。',
  },
]

const workflowSteps = [
  { label: 'JD 输入', desc: '粘贴目标岗位 JD' },
  { label: 'JD 解析', desc: '提取结构化岗位画像' },
  { label: '出题', desc: '生成定制面试题 + 追问树' },
  { label: '面试追问', desc: '多轮对话 + 动态追问' },
  { label: '四维评估', desc: '独立维度打分' },
  { label: '教练建议', desc: '逐题改进建议 + 范例' },
  { label: 'Judge 复核', desc: '质量检查' },
  { label: '诊断报告', desc: '结构化面试报告' },
]

export default function Home() {
  return (
    <div>
      {/* Hero */}
      <section style={{ textAlign: 'center', padding: '48px 0 40px' }}>
        <h1 style={{ fontSize: '2.2rem', marginBottom: '12px' }}>
          AI 面试训练 Agent
        </h1>
        <p style={{ fontSize: '1.1rem', color: 'var(--color-text-secondary)', maxWidth: 600, margin: '0 auto 24px', lineHeight: 1.7 }}>
          一个会追问、会打分、会给改进建议的 AI 面试教练。
          专为 AI 产品经理 / AI 产品运营 / Agent 产品经理面试设计。
        </p>
        <div style={{ display: 'flex', gap: 12, justifyContent: 'center' }}>
          <Link to="/jd-input" className="btn btn-primary btn-lg">
            开始面试 →
          </Link>
          <Link to="/eval" className="btn btn-secondary btn-lg">
            查看评测面板
          </Link>
        </div>
      </section>

      {/* Disclaimer */}
      <div style={{
        background: '#fffbeb', border: '1px solid #fcd34d', borderRadius: 'var(--radius-sm)',
        padding: '12px 16px', fontSize: '0.85rem', color: '#92400e', marginBottom: 40,
        textAlign: 'center',
      }}>
        ⚠️ 声明：本产品仅供面试准备参考，<strong>不承诺面试通过率</strong>，不替代真实面试官的专业判断。
      </div>

      {/* Features */}
      <section style={{ marginBottom: 40 }}>
        <h2 style={{ marginBottom: 6 }}>核心能力</h2>
        <p className="section-desc" style={{ marginBottom: 20 }}>
          基于 6 Agent 协作管线，覆盖面试训练全流程
        </p>
        <div className="grid-3">
          {features.map((f) => (
            <div key={f.title} className="card" style={{ padding: '20px' }}>
              <div style={{ fontSize: '1.5rem', marginBottom: 8 }}>{f.icon}</div>
              <h3 style={{ fontSize: '0.95rem', marginBottom: 4 }}>{f.title}</h3>
              <p className="text-sm text-secondary">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Workflow */}
      <section style={{ marginBottom: 40 }}>
        <h2 style={{ marginBottom: 6 }}>Agent 工作流</h2>
        <p className="section-desc" style={{ marginBottom: 20 }}>
          7 Phase 管线，每个环节可独立评测和迭代
        </p>
        <div className="card" style={{ padding: '24px 20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: 0 }}>
            {workflowSteps.map((step, i) => (
              <div key={step.label} style={{ display: 'flex', alignItems: 'center', gap: 0 }}>
                <div style={{
                  background: 'var(--color-primary)', color: '#fff',
                  borderRadius: '50%', width: 36, height: 36,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: '0.8rem', fontWeight: 700, flexShrink: 0,
                }}>
                  {i + 1}
                </div>
                <div style={{ marginLeft: 8 }}>
                  <div style={{ fontWeight: 600, fontSize: '0.85rem' }}>{step.label}</div>
                  <div className="text-xs text-muted">{step.desc}</div>
                </div>
                {i < workflowSteps.length - 1 && (
                  <div style={{
                    width: 32, height: 1, background: 'var(--color-border)',
                    margin: '0 8px', flexShrink: 0,
                  }} />
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Tech */}
      <section>
        <h2 style={{ marginBottom: 6 }}>技术亮点（作品集视角）</h2>
        <p className="section-desc" style={{ marginBottom: 20 }}>
          展示 AI 产品经理的核心竞争力
        </p>
        <div className="grid-2">
          <div className="card">
            <h3>Agent Team 架构</h3>
            <p className="text-sm text-secondary mt-8">
              6 个独立 Agent 各司其职，Orchestrator 管线串联。每个 Agent 有独立的 Prompt、输入输出 Schema、约束条件和评测标准。非端到端黑盒。
            </p>
          </div>
          <div className="card">
            <h3>评测体系</h3>
            <p className="text-sm text-secondary mt-8">
              4 套评测集覆盖 JD 解析、出题质量、评估一致性、教练可用性。量化指标驱动迭代，Badcase 分类 → 根因分析 → 修复 → 回归评测的完整闭环。
            </p>
          </div>
        </div>
      </section>
    </div>
  )
}
