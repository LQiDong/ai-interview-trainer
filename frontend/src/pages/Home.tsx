import {
  ArrowRight, Brain, Briefcase, ChartPolar, Check, Code, Compass,
  CrownSimple, ShieldCheck, Sparkle, Target, TrendUp, UsersThree,
} from '@phosphor-icons/react'
import { Link } from 'react-router-dom'
import { useEffect } from 'react'
import { useLocation } from 'react-router-dom'

const roles = [
  { icon: Brain, title: 'Agent 开发工程师', desc: '覆盖 Agent 架构、工具调用、RAG、评测与可靠性设计。', tags: ['Agent 架构', 'Python', 'LLM 评测'] },
  { icon: Compass, title: 'AI 产品经理', desc: '覆盖需求判断、产品设计、指标体系与跨团队推进。', tags: ['产品策略', 'AI 产品', '商业化'] },
  { icon: Code, title: '全栈工程师', desc: '覆盖前后端架构、API 设计、数据库与工程化交付。', tags: ['React', 'Node.js', '系统设计'] },
  { icon: Briefcase, title: '通用产品经理', desc: '覆盖用户洞察、方案设计、数据分析与项目推进。', tags: ['用户研究', '数据分析', '项目管理'] },
]

const capabilities = [
  { icon: Target, title: '针对真实 JD 出题', desc: '自动识别岗位层级、核心能力和业务场景，不再刷千篇一律的题库。' },
  { icon: UsersThree, title: '像面试官一样追问', desc: '根据回答中的信息缺口继续下探，让每一次练习接近真实压力。' },
  { icon: ChartPolar, title: '四维诊断报告', desc: '从内容、结构、证据和表达四个维度，解释每一个失分点。' },
  { icon: TrendUp, title: '把建议变成练习', desc: '给出下一次能直接套用的改写示例和可执行训练动作。' },
]

const plans = [
  { name: '体验版', price: '0', unit: '永久免费', desc: '先跑通一次完整训练', features: ['1 次完整模拟面试', '基础四维评分', '岗位 JD 智能解析'], cta: '免费开始', featured: false },
  { name: '求职冲刺', price: '39', unit: '元 / 月', desc: '适合正在集中面试的求职者', features: ['每月 20 次模拟面试', '深度追问与完整报告', '历史报告与成长对比', '优先生成与更长回答'], cta: '开始冲刺', featured: true },
  { name: '职业成长', price: '99', unit: '元 / 季', desc: '适合长期能力建设', features: ['每季 80 次模拟面试', '全部岗位题型', '季度能力复盘', '新功能优先体验'], cta: '选择季卡', featured: false },
]

export default function Home() {
  const location = useLocation()
  useEffect(() => {
    const section = new URLSearchParams(location.search).get('section')
    if (section) requestAnimationFrame(() => document.getElementById(section)?.scrollIntoView({ behavior: 'smooth' }))
  }, [location.search])

  return (
    <div className="home-page">
      <section className="hero commercial-hero">
        <div className="hero-copy">
          <div className="eyebrow"><Sparkle weight="fill" />不背标准答案，练出能经得住追问的表达</div>
          <h1>下一场面试，<br />让你的经历更有说服力。</h1>
          <p>粘贴目标岗位 JD，完成一场会追问的 AI 模拟面试。20 分钟后，拿到清晰的能力诊断和下一步练习方案。</p>
          <div className="hero-actions">
            <Link to="/jd-input" className="btn btn-primary btn-lg">免费开始训练 <ArrowRight /></Link>
            <a href="#roles" className="btn btn-secondary btn-lg">查看支持岗位</a>
          </div>
          <div className="hero-note"><ShieldCheck />无需注册即可体验，报告仅供求职准备参考</div>
        </div>

        <div className="hero-product" aria-label="面试能力诊断报告预览">
          <div className="preview-topbar"><span>本次训练诊断</span><span className="preview-status">已完成</span></div>
          <div className="preview-role">AI 产品经理 · 中高级</div>
          <div className="preview-score">
            <div><small>综合表现</small><strong>2.4</strong><span>/ 3.0</span></div>
            <span className="score-label">达到岗位预期</span>
          </div>
          <div className="preview-divider" />
          <div className="preview-list">
            {[['内容匹配度', '2.7'], ['结构清晰度', '2.3'], ['证据支撑度', '1.8'], ['表达可信度', '2.6']].map(([label, score], index) => (
              <div className="preview-row" key={label}><span><i>{index + 1}</i>{label}</span><strong>{score}</strong></div>
            ))}
          </div>
          <div className="preview-action"><span><Target weight="fill" /></span><div><small>下一步优先练习</small><strong>用 STAR 结构补足量化证据</strong></div></div>
        </div>
      </section>

      <section className="proof-strip" aria-label="一次训练包含">
        <span>一次完整训练包含</span>
        {['目标岗位分析', '7 道定制问题', '多轮动态追问', '可解释诊断报告'].map(item => <strong key={item}><Check weight="bold" />{item}</strong>)}
      </section>

      <section className="home-section roles-section" id="roles">
        <div className="section-heading"><span>热门岗位</span><h2>选定方向，开始一场更像真实招聘的练习</h2><p>不同岗位使用不同的能力模型、问题结构和评价标准。你也可以直接粘贴任意岗位 JD。</p></div>
        <div className="role-grid">
          {roles.map(({ icon: Icon, title, desc, tags }) => (
            <Link className="role-item" to={`/jd-input?role=${encodeURIComponent(title)}`} key={title}>
              <div className="role-icon"><Icon weight="duotone" /></div><ArrowRight className="role-arrow" />
              <h3>{title}</h3><p>{desc}</p><div className="role-tags">{tags.map(tag => <span key={tag}>{tag}</span>)}</div>
            </Link>
          ))}
        </div>
      </section>

      <section className="capability-section">
        <div className="section-heading"><span>为什么有效</span><h2>从一次练习，到一套可以重复的进步方法</h2></div>
        <div className="capability-list">
          {capabilities.map(({ icon: Icon, title, desc }, index) => <article key={title}><span>{String(index + 1).padStart(2, '0')}</span><Icon weight="duotone" /><div><h3>{title}</h3><p>{desc}</p></div></article>)}
        </div>
      </section>

      <section className="pricing-section" id="pricing">
        <div className="section-heading"><span>简单定价</span><h2>先免费体验，准备进入面试期再升级</h2><p>当前页面为商业化方案展示，支付接入前不会产生实际扣费。</p></div>
        <div className="pricing-grid">
          {plans.map(plan => <article className={`pricing-plan ${plan.featured ? 'featured' : ''}`} key={plan.name}>
            {plan.featured && <div className="plan-badge"><CrownSimple weight="fill" />推荐</div>}
            <h3>{plan.name}</h3><p>{plan.desc}</p><div className="plan-price"><strong>¥{plan.price}</strong><span>{plan.unit}</span></div>
            <ul>{plan.features.map(feature => <li key={feature}><Check weight="bold" />{feature}</li>)}</ul>
            <Link to="/jd-input" className={`btn ${plan.featured ? 'btn-primary' : 'btn-secondary'}`}>{plan.cta}<ArrowRight /></Link>
          </article>)}
        </div>
      </section>

      <section className="closing-cta">
        <div><span>从目标岗位开始</span><h2>把“我做过”，练成“我能证明”。</h2></div>
        <Link to="/jd-input" className="btn btn-primary btn-lg">开始免费模拟面试 <ArrowRight /></Link>
      </section>
    </div>
  )
}
