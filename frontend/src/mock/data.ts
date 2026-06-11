// ── Mock: Job Profile ─────────────────────────────────────────────
export const mockJobProfile = {
  position: {
    title: 'AI产品经理',
    level: '高级',
    inferred_category: 'AI产品经理',
  },
  company_context: {
    industry: '企业服务/SaaS',
    product_type: 'AI Agent 开发平台',
    team_size_hint: '中型团队',
  },
  responsibilities: [
    { description: '负责AI Agent平台的产品规划和设计', importance: 'core', keywords: ['Agent平台', '产品规划'] },
    { description: '与工程、算法团队协作，推动产品从0到1落地', importance: 'core', keywords: ['跨团队协作', '0到1'] },
    { description: '制定产品路线图并跟踪关键指标', importance: 'secondary', keywords: ['产品路线图', '指标体系'] },
  ],
  hard_skills: [
    { skill: 'Agent架构设计', requirement_level: '必须', evidence_from_jd: '熟悉Multi-Agent协作机制' },
    { skill: 'Prompt Engineering', requirement_level: '必须', evidence_from_jd: '能设计高质量Agent指令' },
    { skill: '数据分析', requirement_level: '加分', evidence_from_jd: '数据驱动产品决策' },
  ],
  soft_skills: [
    { skill: '跨团队协作', requirement_level: '必须', evidence_from_jd: '高效协作' },
    { skill: '沟通表达', requirement_level: '加分', evidence_from_jd: '复杂概念转化' },
  ],
  experience_requirements: {
    years: '3-5年',
    specific_experience: ['有AI产品从0到1经验', '有B端产品经验'],
    industry_preference: 'AI/企业服务优先',
  },
  interview_focus_areas: [
    { area: 'Agent产品方法论', priority: '高', rationale: '核心考察点' },
    { area: 'B端产品设计', priority: '高', rationale: '核心考察点' },
    { area: '数据驱动决策', priority: '中', rationale: '重要' },
    { area: 'AI技术理解', priority: '中', rationale: '辅助判断' },
  ],
  confidence: { overall: 'high', low_confidence_fields: [], notes: '' },
}

// ── Mock: Question Set ────────────────────────────────────────────
export const mockQuestions = {
  questions: [
    { id: 1, type: 'behavioral', difficulty: 'medium', dimension: '经验匹配',
      question_text: '请做一个自我介绍，重点说说你在AI产品方向的经验和项目。' },
    { id: 2, type: 'case_study', difficulty: 'medium', dimension: '问题解决',
      question_text: '请描述你在AI产品工作中遇到的最复杂的一个问题，以及你是如何解决的。' },
    { id: 3, type: 'knowledge', difficulty: 'medium', dimension: '专业深度',
      question_text: '你如何理解Multi-Agent协作？你认为一个好的Agent产品应该具备哪些核心能力？' },
    { id: 4, type: 'case_study', difficulty: 'medium', dimension: '数据驱动',
      question_text: '请描述一个你通过数据分析驱动产品决策的具体案例。' },
    { id: 5, type: 'situational', difficulty: 'medium', dimension: '沟通协作',
      question_text: '当你和工程团队对产品方向有分歧时，你会如何处理？' },
    { id: 6, type: 'knowledge', difficulty: 'hard', dimension: '专业深度',
      question_text: '你如何评估一个AI产品的用户体验质量？请给出你的评估框架。' },
    { id: 7, type: 'behavioral', difficulty: 'medium', dimension: '综合',
      question_text: '请用3分钟说服我们，为什么你是这个岗位的合适人选。' },
  ],
}

// ── Mock: Evaluation ──────────────────────────────────────────────
export const mockEvaluation = {
  evaluation_meta: {
    position_level_anchor: '高级',
    total_questions_evaluated: 7,
  },
  per_question_scores: [
    {
      question_id: 1, question_text: '自我介绍与AI产品经验',
      content_relevance: { score: 2, max_score: 3, evidence: '基本覆盖岗位核心要求领域，但未针对Agent PM方向重点展开',
        deduction_points: ['自我介绍未针对Agent PM岗位做定制化调整'], hit_points: ['有AI产品项目经验', '表达流畅'] },
      structure_clarity: { score: 2, max_score: 3, evidence: '有时间线逻辑，但缺少总-分结构',
        deduction_points: ['缺少能力概览——直接按时间线展开'], hit_points: ['时间线组织合理'] },
      evidence_support: { score: 1, max_score: 3, evidence: '提到参与过AI项目但未给出具体数据',
        deduction_points: ['缺少具体项目数据', '未量化个人贡献'], hit_points: ['有尝试举例'] },
      expression_credibility: { score: 2, max_score: 3, evidence: '表达自然，无背诵痕迹',
        deduction_points: [], hit_points: ['语气自然', '无过度包装'] },
    },
    {
      question_id: 2, question_text: '最复杂的AI产品问题及解决方案',
      content_relevance: { score: 1, max_score: 3, evidence: '描述了问题但偏向执行层面',
        deduction_points: ['未展示AI产品经理特有的分析思维', '问题定义不够精准'], hit_points: ['有实际案例'] },
      structure_clarity: { score: 1, max_score: 3, evidence: '因果链不清晰',
        deduction_points: ['因果推导缺失'], hit_points: ['尝试结构化表达'] },
      evidence_support: { score: 1, max_score: 3, evidence: '数据缺少基线和衡量方式',
        deduction_points: ['"提升30%"未说明基线和归因'], hit_points: ['有量化意识'] },
      expression_credibility: { score: 2, max_score: 3, evidence: '表达真诚',
        deduction_points: [], hit_points: ['诚实坦率'] },
    },
    {
      question_id: 3, question_text: 'Multi-Agent协作的理解',
      content_relevance: { score: 2, max_score: 3, evidence: '对Agent概念有基本理解',
        deduction_points: ['对Agent产品核心能力的阐述缺少框架感'], hit_points: ['概念理解基本准确'] },
      structure_clarity: { score: 2, max_score: 3, evidence: '有分类讨论意识',
        deduction_points: ['分类不够MECE'], hit_points: ['尝试分类'] },
      evidence_support: { score: 1, max_score: 3, evidence: '理论为主，缺少落地案例',
        deduction_points: ['未结合实际项目经验'], hit_points: [] },
      expression_credibility: { score: 2, max_score: 3, evidence: '表达流畅',
        deduction_points: [], hit_points: ['术语使用准确'] },
    },
    {
      question_id: 4, question_text: '数据驱动决策案例',
      content_relevance: { score: 1, max_score: 3, evidence: '描述了数据分析过程但深度不足',
        deduction_points: ['未展示A/B测试等专业方法论的运用'], hit_points: ['有数据意识'] },
      structure_clarity: { score: 2, max_score: 3, evidence: '问题→分析→结论结构清晰',
        deduction_points: ['分析过程逻辑链可更严密'], hit_points: ['框架意识好'] },
      evidence_support: { score: 1, max_score: 3, evidence: '数据描述模糊',
        deduction_points: ['数据来源、样本量、置信度均未提及'], hit_points: ['有量化导向'] },
      expression_credibility: { score: 2, max_score: 3, evidence: '自然表达',
        deduction_points: [], hit_points: ['有自我反思'] },
    },
    {
      question_id: 5, question_text: '与工程团队分歧处理',
      content_relevance: { score: 2, max_score: 3, evidence: '回答了处理方式但偏向理论',
        deduction_points: ['案例不够具体'], hit_points: ['思路清晰'] },
      structure_clarity: { score: 2, max_score: 3, evidence: '有步骤意识',
        deduction_points: ['步骤之间的关联可更紧密'], hit_points: ['逻辑线清楚'] },
      evidence_support: { score: 1, max_score: 3, evidence: '缺少真实案例',
        deduction_points: ['纯方法论，无实际冲突案例'], hit_points: [] },
      expression_credibility: { score: 2, max_score: 3, evidence: '表达自然',
        deduction_points: [], hit_points: ['态度积极'] },
    },
    {
      question_id: 6, question_text: 'AI产品UX质量评估框架',
      content_relevance: { score: 1, max_score: 3, evidence: '有框架思路但不够系统',
        deduction_points: ['未区分AI产品的特殊评估维度（如准确性、幻觉率）'], hit_points: ['有框架意识'] },
      structure_clarity: { score: 1, max_score: 3, evidence: '框架维度之间存在重叠',
        deduction_points: ['框架不MECE'], hit_points: ['尝试结构化'] },
      evidence_support: { score: 0, max_score: 3, evidence: '纯理论框架，无验证案例',
        deduction_points: ['未用任何案例验证框架有效性'], hit_points: [] },
      expression_credibility: { score: 2, max_score: 3, evidence: '表达自然',
        deduction_points: [], hit_points: ['对AI产品有思考'] },
    },
    {
      question_id: 7, question_text: '为什么你是合适人选',
      content_relevance: { score: 2, max_score: 3, evidence: '总结了自身优势',
        deduction_points: ['未与JD要求做一一对应'], hit_points: ['有自我认知'] },
      structure_clarity: { score: 2, max_score: 3, evidence: '有总结结构',
        deduction_points: ['亮点分散，未形成合力'], hit_points: ['有归纳意识'] },
      evidence_support: { score: 1, max_score: 3, evidence: '优势陈述缺少证据链',
        deduction_points: ['每个优势都缺少具体案例支撑'], hit_points: [] },
      expression_credibility: { score: 2, max_score: 3, evidence: '真诚',
        deduction_points: [], hit_points: ['态度积极'] },
    },
  ],
  dimension_summary: {
    content_relevance: { average_score: 1.57, max_score: 3,
      overall_assessment: '基本能命中考点，但深度和针对性不足',
      top_weakness: '未针对Agent PM岗位做定制化回答',
      top_strength: '有AI产品基础认知' },
    structure_clarity: { average_score: 1.71, max_score: 3,
      overall_assessment: '有一定结构意识但逻辑链不完整',
      top_weakness: '因果关系推导跳跃',
      top_strength: '有框架意识' },
    evidence_support: { average_score: 0.86, max_score: 3,
      overall_assessment: '最突出的短板——几乎所有回答都缺乏具体证据',
      top_weakness: '数据缺乏基线和衡量方式',
      top_strength: '有量化意识' },
    expression_credibility: { average_score: 2.0, max_score: 3,
      overall_assessment: '表达整体真诚自然',
      top_weakness: '偶有概念混淆',
      top_strength: '真诚坦率、不包装' },
  },
  overall_assessment: {
    weighted_total_score: 1.47,
    max_score: 3,
    summary: '候选人展现出AI产品基础认知和一定的项目经验，表达真诚。主要短板：证据支撑度严重不足，量化思维薄弱。',
    interview_performance_level: '中等偏下——距通过门槛有一定差距，但提升空间明确',
  },
}

// ── Mock: Coaching ────────────────────────────────────────────────
export const mockCoaching = {
  coaching_meta: {
    improvement_priority: 'evidence_support',
    priority_rationale: '证据支撑度是最短板（均分0.86），直接影响其他维度表现',
    total_action_items: 6,
  },
  per_question_coaching: [
    {
      question_id: 1, question_text: '自我介绍与AI产品经验', overall_question_score: 1.75,
      coaching_entries: [
        { target_dimension: 'evidence_support', target_score: 1,
          deduction_point_from_evaluator: '缺少具体项目数据，未量化个人贡献',
          why_it_matters: '面试官无法判断你"参与过"和"主导过"的区别',
          how_to_improve: '每次自我介绍时，每个项目用一句话带出核心数据。格式：我主导了XX项目，[指标]从A提升到B（+X%），核心归因是Y',
          example_better_response: '我过去3年主导了2个AI产品项目。第一个是Agent平台的工具调用模块，我将调用成功率从78%提升到94%，延迟降低65%，这个项目让我深入理解了Agent的可靠性设计。第二个是…' },
        { target_dimension: 'content_relevance', target_score: 2,
          deduction_point_from_evaluator: '自我介绍未针对Agent PM岗位做定制化调整',
          why_it_matters: '你的自我介绍应该是一个"论点"——即"我是这个岗位的合适人选"，而非一个"时间线"',
          how_to_improve: '面试前做"JD-能力映射"：把JD每一条核心要求映射为你的一段经验',
          example_better_response: '我认为我适合这个Agent PM岗位，原因有三：第一，我有Agent产品从0到1的实操经验…第二，我擅长跨团队协作…第三…' },
      ],
    },
    {
      question_id: 2, question_text: '最复杂的AI产品问题及解决方案', overall_question_score: 1.25,
      coaching_entries: [
        { target_dimension: 'evidence_support', target_score: 1,
          deduction_point_from_evaluator: '"提升30%"未说明基线和归因',
          why_it_matters: '没有基线的数据是无效数据。面试官会怀疑数据的可信度',
          how_to_improve: '使用"基线→动作→变化→归因"四步法。每天拿一个项目练习，直到成为肌肉记忆',
          example_better_response: '优化前工具调用成功率为78%（基线：500次人工抽检）。我做了三个改动：…上线后提升至94%（同口径），净提升16pp。归因分析显示B改动贡献了60%的效果。' },
        { target_dimension: 'structure_clarity', target_score: 1,
          deduction_point_from_evaluator: '因果推导缺失',
          why_it_matters: '面试官听你的回答像是在看"点"而非"线"——缺少因果链会让思路显得跳跃',
          how_to_improve: '练习"因果链表达法"：每次描述决策时强制说出"因为A→所以B→导致C→因此做了D→结果E"',
          example_better_response: '因为用户反馈工具调用经常失败(A)，所以我们分析了500次调用日志，发现60%失败是因为参数格式不匹配(B)，这导致用户平均浪费30秒手动重试(C)。因此我们设计了参数自动校验和重试机制(D)，最终将失败率从22%降至6%(E)。' },
      ],
    },
  ],
  top_3_actions: [
    { rank: 1, action: '建立"量化表达习惯"——每个项目案例强制填写基线、动作、变化、归因',
      target_dimension: 'evidence_support', expected_impact: '可将证据支撑度从0.86显著提升',
      practice_method: '拿出最近3个项目，每个用4句话写清楚基线→动作→变化→归因',
      time_estimate: '2周集中练习' },
    { rank: 2, action: '面试前做"JD-能力映射表"——每条JD要求对应一个具体案例',
      target_dimension: 'content_relevance', expected_impact: '可显著提升回答的岗位匹配度',
      practice_method: '拿出3份目标岗位JD，逐一做映射练习',
      time_estimate: '1周' },
    { rank: 3, action: '练习"因果链表达法"——用完整的因果逻辑链描述每个决策',
      target_dimension: 'structure_clarity', expected_impact: '提升回答的可跟随性和说服力',
      practice_method: '每天选一个工作决策用因果链写出，录音自查',
      time_estimate: '1周' },
  ],
  dimension_improvement_plan: {
    content_relevance: { current_avg: 1.57, target_avg: 2.5, improvement_strategy: '做JD-能力映射表', priority: '中' },
    structure_clarity: { current_avg: 1.71, target_avg: 2.5, improvement_strategy: '强化因果链表达', priority: '中' },
    evidence_support: { current_avg: 0.86, target_avg: 2.5, improvement_strategy: '头号改进维度', priority: '最高' },
    expression_credibility: { current_avg: 2.0, target_avg: 2.5, improvement_strategy: '保持真诚优势，补充术语准确性', priority: '低' },
  },
  general_advice: '你在AI产品方向有不错的基础，表达也真诚自然。当前最大的成长杠杆是"量化表达"——你的项目经验并不差，但你描述它们的方式让面试官难以评估真实影响力。建议接下来两周集中训练"每个观点都有证据"的肌肉记忆。',
}

// ── Mock: Judge ───────────────────────────────────────────────────
export const mockJudge = {
  judge_meta: { overall_verdict: 'pass_with_issues' },
  check_results: {
    score_evidence_consistency: { passed: true, total_issues: 0, critical_issues: 0, high_severity_issues: 0, issues: [] },
    low_score_deduction_completeness: { passed: true, total_issues: 1, critical_issues: 0, high_severity_issues: 0,
      issues: [{ question_id: 6, dimension: 'evidence_support', score_given: 0, severity: 'low',
        detail: 'Q6证据支撑度为0分，扣分点可更具体地指出期望的证据类型',
        recommendation: '建议补充期望：引用的行业报告、用户反馈数据、或A/B测试结果' }] },
    coach_evaluator_alignment: { passed: true, total_issues: 0, critical_issues: 0, high_severity_issues: 0, issues: [] },
    over_promise_detection: { passed: true, total_issues: 1, critical_issues: 0, high_severity_issues: 0,
      issues: [{ source: 'coach', location: 'top_3_actions[0].expected_impact',
        text: '可将证据支撑度从0.86显著提升', finding: 'borderline_over_promise', severity: 'low',
        detail: '数值预测建议加注"在认真练习的前提下"',
        recommendation: '建议弱化为"预期可帮助改善"' }] },
  },
  overall_verdict: 'pass_with_issues',
  verdict_rationale: '四项检查均通过或仅有低严重度发现。整体质量可接受，无需阻断报告发布。',
}

// ── Mock: Eval Dashboard ──────────────────────────────────────────
export const mockEvalMetrics = {
  jd_parse_f1: 0.82,
  question_relevance_mean: 4.1,
  eval_mae: 0.48,
  coach_usability: 0.74,
  judge_detection: 0.85,
}

export const mockEvalDetails = [
  { id: 1, agent: 'JD Parser', metric: 'F1 Score', value: 0.82, target: 0.80, status: 'pass' },
  { id: 2, agent: 'JD Parser', metric: '关键字段召回', value: 0.88, target: 0.80, status: 'pass' },
  { id: 3, agent: '出题官', metric: '题目相关性', value: 4.1, target: 3.8, status: 'pass' },
  { id: 4, agent: '出题官', metric: '难度匹配度', value: 3.6, target: 3.8, status: 'warn' },
  { id: 5, agent: '评估官', metric: 'MAE (vs 人工)', value: 0.48, target: 0.50, status: 'pass' },
  { id: 6, agent: '评估官', metric: '评分一致性', value: 0.76, target: 0.75, status: 'pass' },
  { id: 7, agent: '教练', metric: '建议可用率', value: 0.74, target: 0.70, status: 'pass' },
  { id: 8, agent: '教练', metric: '建议覆盖率', value: 0.82, target: 0.85, status: 'warn' },
  { id: 9, agent: 'Judge', metric: 'badcase检出率', value: 0.85, target: 0.80, status: 'pass' },
  { id: 10, agent: 'Judge', metric: '误报率', value: 0.12, target: 0.15, status: 'pass' },
]

export const mockBadcases = [
  { id: 1, agent: '评估官', type: '评分矛盾', severity: 'P0', description: 'Q3内容匹配度得分2但evidence描述了严重偏题',
    root_cause: 'Prompt对"偏题"的界定不够清晰', status: '已修复', fix: '在评分锚定标准中增加了"答非所问→0分"的明确规则' },
  { id: 2, agent: '面试官', type: '追问跑偏', severity: 'P1', description: '候选人回答Agent记忆后，面试官追问了完全无关的数据库问题',
    root_cause: '追问树触发条件过于宽泛，关键词匹配误触发', status: '已修复', fix: '追问触发增加了语义相似度阈值' },
  { id: 3, agent: '教练', type: '建议空洞', severity: 'P1', description: '教练建议为"多练习产品思维"，无法执行',
    root_cause: '教练Prompt缺少"反例"约束', status: '已修复', fix: '增加了无效建议黑名单和可行动性检查' },
  { id: 4, agent: 'JD Parser', type: 'JD误读', severity: 'P1', description: '将"AI产品运营"解析为"AI产品经理"',
    root_cause: 'JD中产品运营关键词占比低，模型默认归类为产品经理', status: '修复中', fix: '增加运营类关键词权重' },
  { id: 5, agent: '评估官', type: '评分矛盾', severity: 'P0', description: '结构清晰度3分但evidence说"逻辑混乱"',
    root_cause: 'LLM在评分和evidence生成时的自洽性不足', status: '已修复', fix: '评估官输出前增加了自洽检查环节（Judge复用）' },
  { id: 6, agent: '教练', type: '过度承诺', severity: 'P2', description: '教练说"按照这个方法练习一定能通过面试"',
    root_cause: '教练Prompt虽有限制但未在输出解析时做硬拦截', status: '已修复', fix: '增加正则硬拦截+Judge检查4覆盖' },
  { id: 7, agent: '面试官', type: '语气不当', severity: 'P2', description: '面试官追问语气过于生硬："你这个回答完全不对"',
    root_cause: '面试官Prompt中追问语气约束不够具体', status: '已修复', fix: '增加了追问语气的具体约束和反例' },
  { id: 8, agent: '出题官', type: '难度失配', severity: 'P2', description: '对初级岗位出了专家级Agent架构设计题',
    root_cause: '出题逻辑未读取position.level字段', status: '已修复', fix: '出题时显式传入position.level并做难度校准' },
]

export const mockAiVsHuman = [
  { question_id: 1, dimension: '内容匹配度', ai_score: 2, human_avg: 2.2, delta: -0.2 },
  { question_id: 1, dimension: '结构清晰度', ai_score: 2, human_avg: 1.8, delta: +0.2 },
  { question_id: 1, dimension: '证据支撑度', ai_score: 1, human_avg: 1.3, delta: -0.3 },
  { question_id: 1, dimension: '表达可信度', ai_score: 2, human_avg: 1.9, delta: +0.1 },
  { question_id: 2, dimension: '内容匹配度', ai_score: 1, human_avg: 1.4, delta: -0.4 },
  { question_id: 2, dimension: '结构清晰度', ai_score: 1, human_avg: 1.2, delta: -0.2 },
  { question_id: 2, dimension: '证据支撑度', ai_score: 1, human_avg: 1.1, delta: -0.1 },
  { question_id: 2, dimension: '表达可信度', ai_score: 2, human_avg: 1.8, delta: +0.2 },
]
