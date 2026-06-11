"""
LLM Client abstraction — supports mock mode and real API calls.

Environment variables:
  MODEL_PROVIDER: "mock" (default) | "openai" | "anthropic" | "openrouter"
  API_KEY: your API key (required for non-mock providers)
  MODEL_NAME: override the default model name
  API_BASE_URL: override the API base URL (e.g. OpenRouter)
"""

from __future__ import annotations

import json
import os
import re
from typing import Optional

import httpx
from dotenv import load_dotenv

load_dotenv()

MODEL_PROVIDER = os.getenv("MODEL_PROVIDER", "mock").lower()
API_KEY = os.getenv("API_KEY", "")
MODEL_NAME = os.getenv("MODEL_NAME", "")
API_BASE_URL = os.getenv("API_BASE_URL", "")

# ── Default model per provider ──────────────────────────────────────

DEFAULT_MODELS = {
    "openai": "gpt-4o",
    "anthropic": "claude-sonnet-4-6",
    "openrouter": "anthropic/claude-sonnet-4-6",
    "mock": "mock",
}


def get_model_name() -> str:
    return MODEL_NAME or DEFAULT_MODELS.get(MODEL_PROVIDER, "mock")


# ── Mock response builders ──────────────────────────────────────────

def _mock_jd_parser_response(_user_message: str) -> str:
    """Return a mock JobProfile based on the user's JD text."""
    return json.dumps({
        "position": {
            "title": "AI产品经理",
            "level": "高级",
            "inferred_category": "AI产品经理"
        },
        "company_context": {
            "industry": "企业服务/SaaS",
            "product_type": "AI Agent 开发平台",
            "team_size_hint": "未提及"
        },
        "responsibilities": [
            {
                "description": "负责AI Agent平台的产品规划和设计",
                "importance": "core",
                "keywords": ["Agent平台", "产品规划"]
            },
            {
                "description": "与工程、算法团队协作，推动产品从0到1落地",
                "importance": "core",
                "keywords": ["跨团队协作", "0到1"]
            },
            {
                "description": "制定产品路线图并跟踪关键指标",
                "importance": "secondary",
                "keywords": ["产品路线图", "指标体系"]
            }
        ],
        "hard_skills": [
            {
                "skill": "Agent架构设计",
                "requirement_level": "必须",
                "evidence_from_jd": "熟悉Multi-Agent协作机制，有Agent产品落地经验"
            },
            {
                "skill": "Prompt Engineering",
                "requirement_level": "必须",
                "evidence_from_jd": "能设计高质量的Agent指令和评估策略"
            },
            {
                "skill": "数据分析",
                "requirement_level": "加分",
                "evidence_from_jd": "能用数据驱动产品决策"
            }
        ],
        "soft_skills": [
            {
                "skill": "跨团队协作",
                "requirement_level": "必须",
                "evidence_from_jd": "能与工程、算法、设计团队高效协作"
            },
            {
                "skill": "沟通表达",
                "requirement_level": "加分",
                "evidence_from_jd": "能将复杂技术概念转化为用户可理解的语言"
            }
        ],
        "experience_requirements": {
            "years": "3-5年",
            "specific_experience": ["有AI产品从0到1经验", "有B端产品经验"],
            "industry_preference": "AI/企业服务优先"
        },
        "interview_focus_areas": [
            {
                "area": "Agent产品方法论",
                "priority": "高",
                "rationale": "JD反复强调Agent相关能力，推断为核心考察点"
            },
            {
                "area": "B端产品设计",
                "priority": "高",
                "rationale": "产品面向企业用户，核心考察B端思维"
            },
            {
                "area": "数据驱动决策",
                "priority": "中",
                "rationale": "JD提及指标体系但非核心要求"
            },
            {
                "area": "AI技术理解",
                "priority": "中",
                "rationale": "需要与技术团队深度协作"
            }
        ],
        "confidence": {
            "overall": "high",
            "low_confidence_fields": [],
            "notes": "JD信息完整，关键字段均可明确提取（Mock模式）"
        }
    }, ensure_ascii=False)


def _mock_interviewer_response(user_message: str, context: dict) -> str:
    """Return a mock interviewer action based on context."""
    transcript = context.get("transcript", [])
    question_index = context.get("current_question_index", 0)
    total_questions = context.get("total_questions", 7)
    follow_up_depth = context.get("current_follow_up_depth", 0)

    questions = [
        "请做一个自我介绍，重点说说你在AI产品方向的经验和项目。",
        "请描述你在AI产品工作中遇到的最复杂的一个问题，以及你是如何解决的。",
        "你如何理解Multi-Agent协作？在你看来，一个好的Agent产品应该具备哪些核心能力？",
        "请描述一个你通过数据分析驱动产品决策的具体案例。",
        "当你和工程团队对产品方向有分歧时，你会如何处理？",
        "你如何评估一个AI产品的用户体验质量？请给出你的评估框架。",
        "请用3分钟说服我，为什么你是这个岗位的合适人选。"
    ]

    follow_ups = [
        ["你说的是项目背景，能否具体说说你在其中的角色和决策？",
         "你提到了技术挑战，能否展开说说具体是什么技术问题？",
         "听起来这是一个团队成果，你的个人贡献具体体现在哪里？"],
        ["如果能重来一次，你会怎么做不同的决策？",
         "这个方案有没有替代方案？你为什么选择了当前这个？",
         "你是如何衡量这个解决方案的效果的？"],
        ["你能否举一个具体的场景说明Agent协作中的难点？",
         "Agent之间的通信协议你是怎么设计的？",
         "工具调用的可靠性你是怎么保证的？"],
        ["这个数据结论有没有做置信度检验？",
         "如果数据支持A方案但你的直觉支持B方案，你怎么决策？",
         "你如何确保数据不会误导你的产品判断？"],
        ["能否举一个你和工程团队在技术可行性上有分歧的具体案例？",
         "如果工程团队说'做不了'，你会怎么处理？",
         "你是如何平衡技术理想和业务现实的？"],
        ["你提到了可用性，具体用量化指标来定义一下？",
         "你如何区分'用户不喜欢这个功能'和'用户不理解这个功能'？",
         "AI产品的评估和传统产品有什么不同？"],
        ["你觉得你相比其他候选人最大的差异化优势是什么？",
         "你对未来3年AI产品的发展有什么判断？"]
    ]

    # End condition: no more questions
    if question_index >= len(questions):
        return json.dumps({
            "action": "end_interview",
            "summary": {
                "total_questions_asked": len(questions),
                "total_rounds": len(transcript),
                "candidate_apparent_strengths": ["对Agent产品有一定理解"],
                "candidate_apparent_weaknesses": ["量化表达可加强"],
                "notable_moments": []
            },
            "message": "好的，我们的面试到这里就结束了。接下来系统将为你生成详细的评估报告。"
        }, ensure_ascii=False)

    # First question
    if len(transcript) == 0:
        return json.dumps({
            "action": "ask_question",
            "question_id": question_index + 1,
            "question_number": question_index + 1,
            "total_questions": total_questions,
            "follow_up_depth": 0,
            "message": questions[question_index]
        }, ensure_ascii=False)

    # Decide: follow-up or next question
    if follow_up_depth < 3 and question_index < len(follow_ups):
        fu_list = follow_ups[question_index]
        if follow_up_depth < len(fu_list):
            return json.dumps({
                "action": "follow_up",
                "question_id": question_index + 1,
                "follow_up_depth": follow_up_depth + 1,
                "follow_up_reason": f"候选人的回答在第{follow_up_depth + 1}层追问上可以进一步深挖",
                "message": fu_list[follow_up_depth]
            }, ensure_ascii=False)

    # Next question
    next_idx = question_index + 1
    if next_idx >= len(questions):
        return json.dumps({
            "action": "end_interview",
            "summary": {
                "total_questions_asked": len(questions),
                "total_rounds": len(transcript),
                "candidate_apparent_strengths": ["对Agent产品有一定理解"],
                "candidate_apparent_weaknesses": ["量化表达可加强"],
                "notable_moments": []
            },
            "message": "好的，我们的面试到这里就结束了。接下来系统将为你生成详细的评估报告。"
        }, ensure_ascii=False)

    return json.dumps({
        "action": "ask_question",
        "question_id": next_idx + 1,
        "question_number": next_idx + 1,
        "total_questions": total_questions,
        "follow_up_depth": 0,
        "message": questions[next_idx]
    }, ensure_ascii=False)


def _mock_evaluator_response(_user_message: str, context: dict) -> str:
    """Return a mock evaluation with 4-dimension scores."""
    return json.dumps({
        "evaluation_meta": {
            "position_level_anchor": "高级",
            "total_questions_evaluated": context.get("total_questions", 7),
            "evaluation_timestamp": "2026-06-11T00:00:00"
        },
        "per_question_scores": [
            {
                "question_id": 1,
                "question_text": "自我介绍与AI产品经验",
                "content_relevance": {
                    "score": 2, "max_score": 3,
                    "evidence": "候选人介绍了AI产品相关背景，基本覆盖了岗位的核心要求领域，但未针对Agent产品方向做重点展开",
                    "deduction_points": ["自我介绍未针对目标岗位（Agent PM）做定制化调整"],
                    "hit_points": ["有AI产品项目经验背书", "表达流畅"]
                },
                "structure_clarity": {
                    "score": 2, "max_score": 3,
                    "evidence": "结构清晰，有时间线逻辑",
                    "deduction_points": ["缺少'总-分'结构，直接按时间线展开，未先给出能力概览"],
                    "hit_points": ["时间线组织合理"]
                },
                "evidence_support": {
                    "score": 1, "max_score": 3,
                    "evidence": "提到参与过AI项目但未给出具体项目名称、规模、成果数据",
                    "deduction_points": ["缺少具体项目数据", "未量化个人贡献"],
                    "hit_points": ["有尝试举例"]
                },
                "expression_credibility": {
                    "score": 2, "max_score": 3,
                    "evidence": "表达自然，无明显背诵痕迹",
                    "deduction_points": [],
                    "hit_points": ["语气自然", "无过度包装"]
                }
            },
            {
                "question_id": 2,
                "question_text": "最复杂的AI产品问题及解决方案",
                "content_relevance": {
                    "score": 1, "max_score": 3,
                    "evidence": "描述了产品问题但偏向执行层面，未展示AI产品特有的问题分析框架",
                    "deduction_points": ["未展示AI产品经理特有的分析思维", "问题定义不够精准"],
                    "hit_points": ["有实际案例"]
                },
                "structure_clarity": {
                    "score": 1, "max_score": 3,
                    "evidence": "问题→方案结构存在但因果关系不清晰",
                    "deduction_points": ["逻辑链条不完整——'因为…所以…导致…因此做了…'的因果推导缺失"],
                    "hit_points": ["尝试用结构化方式表达"]
                },
                "evidence_support": {
                    "score": 1, "max_score": 3,
                    "evidence": "给出的数据缺少基线和衡量方式",
                    "deduction_points": ["'提升了30%'——未说明基线、衡量口径、归因分析"],
                    "hit_points": ["有量化意识"]
                },
                "expression_credibility": {
                    "score": 2, "max_score": 3,
                    "evidence": "表达真诚，能承认部分结果来自团队协作",
                    "deduction_points": [],
                    "hit_points": ["诚实坦率"]
                }
            }
        ],
        "dimension_summary": {
            "content_relevance": {
                "average_score": 1.5, "max_score": 3,
                "overall_assessment": "基本能命中考点，但深度和针对性不足",
                "top_weakness": "未针对Agent PM岗位做定制化回答",
                "top_strength": "有AI产品基础认知"
            },
            "structure_clarity": {
                "average_score": 1.5, "max_score": 3,
                "overall_assessment": "有一定结构意识但逻辑链不完整",
                "top_weakness": "因果关系推导跳跃",
                "top_strength": "有时间线/框架意识"
            },
            "evidence_support": {
                "average_score": 1.0, "max_score": 3,
                "overall_assessment": "这是本次面试最突出的短板",
                "top_weakness": "几乎所有量化结果都缺少基线和归因",
                "top_strength": "有量化意识"
            },
            "expression_credibility": {
                "average_score": 2.0, "max_score": 3,
                "overall_assessment": "表达整体真诚自然",
                "top_weakness": "偶有概念混淆",
                "top_strength": "真诚坦率、不包装"
            }
        },
        "overall_assessment": {
            "weighted_total_score": 1.45,
            "max_score": 3,
            "summary": "候选人展现出AI产品基础认知和一定的项目经验，表达真诚。主要短板：证据支撑度严重不足，量化思维薄弱；内容深度和针对性有待提升。",
            "interview_performance_level": "中等偏下——距通过门槛有一定差距，但提升空间明确"
        }
    }, ensure_ascii=False)


def _mock_coach_response(_user_message: str, _context: dict) -> str:
    """Return a mock coaching result."""
    return json.dumps({
        "coaching_meta": {
            "improvement_priority": "evidence_support",
            "priority_rationale": "证据支撑度是最短板(均分1.0)，且该维度直接影响内容匹配度无法达3分深度",
            "total_action_items": 6
        },
        "per_question_coaching": [
            {
                "question_id": 1,
                "question_text": "自我介绍与AI产品经验",
                "overall_question_score": 1.75,
                "coaching_entries": [
                    {
                        "target_dimension": "evidence_support",
                        "target_score": 1,
                        "deduction_point_from_evaluator": "缺少具体项目数据，未量化个人贡献",
                        "why_it_matters": "面试官无法判断你'参与过'和'主导过'的区别——缺乏数据会让你的贡献显得模糊",
                        "how_to_improve": "下次自我介绍时，每个项目用一句话带出核心数据。例如：'我主导了XX项目，DAU从A提升到B（+30%），核心归因是我的Y决策'",
                        "example_better_response": "我过去3年主导了2个AI产品项目。第一个是Agent平台的工具调用模块，我将调用成功率从78%提升到94%，延迟降低65%，这个项目让我深入理解了Agent的可靠性设计…"
                    },
                    {
                        "target_dimension": "content_relevance",
                        "target_score": 2,
                        "deduction_point_from_evaluator": "自我介绍未针对Agent PM岗位做定制化调整",
                        "why_it_matters": "你的自我介绍应该是一个'论点'——即'我是这个岗位的合适人选'，而非一个'时间线'",
                        "how_to_improve": "面试前做'JD-能力映射'：把JD的每一条核心要求映射为你的一段经验。自我介绍时先给出总论点（'我适合这个岗位因为三个原因'），再展开",
                        "example_better_response": "我认为我适合这个Agent PM岗位，原因有三：第一，我有Agent产品从0到1的实操经验…第二，我擅长跨团队协作…第三…"
                    }
                ]
            },
            {
                "question_id": 2,
                "question_text": "最复杂的AI产品问题及解决方案",
                "overall_question_score": 1.25,
                "coaching_entries": [
                    {
                        "target_dimension": "evidence_support",
                        "target_score": 1,
                        "deduction_point_from_evaluator": "'提升了30%'——未说明基线、衡量口径、归因分析",
                        "why_it_matters": "没有基线的数据是无效数据。面试官会怀疑'30%'的可信度，甚至质疑你的数据素养",
                        "how_to_improve": "使用'基线→动作→变化→归因'四步法。每天拿一个项目练习，直到成为肌肉记忆",
                        "example_better_response": "优化前工具调用成功率为78%（基线：500次人工抽检）。我做了三个改动：…上线后成功率提升至94%（同口径），净提升16个百分点。归因分析显示…"
                    },
                    {
                        "target_dimension": "structure_clarity",
                        "target_score": 1,
                        "deduction_point_from_evaluator": "逻辑链条不完整——'因为…所以…导致…因此做了…'的因果推导缺失",
                        "why_it_matters": "面试官听你的回答像是在看'点'而非'线'——缺少因果链会让你的思路显得跳跃、难以跟随",
                        "how_to_improve": "练习'因果链表达法'：每次描述决策时强制自己说出'因为A→所以B→导致C→因此我们做了D→结果是E'。录音自查，每缺一环就重录",
                        "example_better_response": "因为用户反馈工具调用经常失败(A)，所以我们分析了500次调用日志，发现60%的失败是因为参数格式不匹配(B)，这导致用户需要手动重试，平均浪费30秒(C)。因此我们设计了参数自动校验和重试机制(D)，最终将失败率从22%降至6%(E)"
                    }
                ]
            }
        ],
        "top_3_actions": [
            {
                "rank": 1,
                "action": "建立'量化表达习惯'——每次准备项目案例时强制填写：基线、动作、变化、归因四个字段",
                "target_dimension": "evidence_support",
                "expected_impact": "预期可将证据支撑度从1.0提升至接近2.0（在认真练习的前提下）",
                "practice_method": "拿出最近3个项目，每个用4句话写清楚基线→动作→变化→归因，找人审核每一环是否可验证",
                "time_estimate": "2周集中练习"
            },
            {
                "rank": 2,
                "action": "面试前做'JD-能力映射表'——将JD每条要求映射为至少一个你准备过的具体案例",
                "target_dimension": "content_relevance",
                "expected_impact": "可显著提升回答的岗位匹配度",
                "practice_method": "拿出3份目标岗位JD，逐一做映射练习",
                "time_estimate": "1周"
            },
            {
                "rank": 3,
                "action": "练习'因果链表达法'——每次描述决策时用'因为…所以…导致…因此…'的完整逻辑链",
                "target_dimension": "structure_clarity",
                "expected_impact": "可提升回答的可跟随性和说服力",
                "practice_method": "每天选一个工作决策用因果链写出，录音后自查是否每一环都有依据",
                "time_estimate": "1周"
            }
        ],
        "dimension_improvement_plan": {
            "content_relevance": {"current_avg": 1.5, "target_avg": 2.5, "improvement_strategy": "做JD-能力映射表，每次回答前先判断题目对应JD的哪个考点", "priority": "中"},
            "structure_clarity": {"current_avg": 1.5, "target_avg": 2.5, "improvement_strategy": "强化因果链——练习用'因为A→所以B→导致C→因此做了D→结果E'完整表达", "priority": "中"},
            "evidence_support": {"current_avg": 1.0, "target_avg": 2.5, "improvement_strategy": "头号改进维度。核心不是'有没有数据'而是'有没有量化思维'。每个观点配证据，每个数据配基线", "priority": "最高"},
            "expression_credibility": {"current_avg": 2.0, "target_avg": 2.5, "improvement_strategy": "保持真诚优势。补充：准备5个专业概念的准确定义，避免面试中用错术语", "priority": "低"}
        },
        "general_advice": "你在AI产品方向有不错的基础，表达也真诚自然。当前最大的成长杠杆是'量化表达'——你的项目经验并不差，但你描述它们的方式让面试官难以评估真实影响力。建议接下来两周集中训练'每个观点都有证据'的肌肉记忆。"
    }, ensure_ascii=False)


def _mock_judge_response(_user_message: str, _context: dict) -> str:
    """Return a mock judge review."""
    return json.dumps({
        "judge_meta": {
            "timestamp": "2026-06-11T00:00:00",
            "evaluation_version": "v1",
            "overall_verdict": "pass_with_issues"
        },
        "check_results": {
            "score_evidence_consistency": {
                "passed": True,
                "total_issues": 0,
                "critical_issues": 0,
                "high_severity_issues": 0,
                "issues": []
            },
            "low_score_deduction_completeness": {
                "passed": True,
                "total_issues": 1,
                "critical_issues": 0,
                "high_severity_issues": 0,
                "issues": [
                    {
                        "question_id": 2,
                        "dimension": "content_relevance",
                        "score_given": 1,
                        "deduction_points": ["未展示AI产品经理特有的分析思维", "问题定义不够精准"],
                        "finding": "deduction_acceptable",
                        "severity": "low",
                        "detail": "扣分点可进一步具体化——'AI产品经理特有的分析思维'指什么？建议补充例子说明期望的分析框架",
                        "recommendation": "建议扣分点改为：'未使用AI产品分析框架（如AARRR、用户旅程地图等）来结构化问题'"
                    }
                ]
            },
            "coach_evaluator_alignment": {
                "passed": True,
                "total_issues": 0,
                "critical_issues": 0,
                "high_severity_issues": 0,
                "issues": []
            },
            "over_promise_detection": {
                "passed": True,
                "total_issues": 1,
                "critical_issues": 0,
                "high_severity_issues": 0,
                "issues": [
                    {
                        "source": "coach",
                        "location": "top_3_actions[0].expected_impact",
                        "text": "预期可将证据支撑度从1.0提升至接近2.0",
                        "finding": "borderline_over_promise",
                        "severity": "low",
                        "detail": "数值预测已加了'在认真练习的前提下'限定，基本可接受，但建议进一步弱化为'预期可帮助改善'",
                        "recommendation": "建议改为'预期可帮助显著改善证据支撑度的表现'"
                    }
                ]
            }
        },
        "overall_verdict": "pass_with_issues",
        "verdict_rationale": "四项检查均通过或仅有低严重度发现。整体质量可接受，无需阻断报告发布。"
    }, ensure_ascii=False)


# ── LLM Client ──────────────────────────────────────────────────────

class LLMClient:
    """Unified LLM client with mock / real mode switching."""

    def __init__(self):
        self.provider = MODEL_PROVIDER
        self.api_key = API_KEY
        self.model = get_model_name()
        self.base_url = API_BASE_URL

    @property
    def mode(self) -> str:
        return "mock" if self.provider == "mock" else "real"

    async def chat(
        self,
        system_prompt: str,
        user_message: str,
        agent_type: str = "",
        context: Optional[dict] = None,
    ) -> str:
        """
        Send a chat completion request.

        Args:
            system_prompt: The system prompt (loaded from prompts/*.md)
            user_message: The user's input / context to process
            agent_type: One of "jd_parser", "interviewer", "evaluator", "coach", "judge"
            context: Additional context dict (e.g. transcript, question index, etc.)

        Returns:
            The LLM's text response (expected to be valid JSON)
        """
        if context is None:
            context = {}

        if self.provider == "mock":
            return self._mock_chat(agent_type, user_message, context)

        return await self._real_chat(system_prompt, user_message)

    def _mock_chat(self, agent_type: str, user_message: str, context: dict) -> str:
        """Return mock JSON responses per agent type."""
        mock_funcs = {
            "jd_parser": _mock_jd_parser_response,
            "interviewer": _mock_interviewer_response,
            "evaluator": _mock_evaluator_response,
            "coach": _mock_coach_response,
            "judge": _mock_judge_response,
        }
        func = mock_funcs.get(agent_type)
        if func is None:
            return json.dumps({"error": f"Unknown agent_type: {agent_type}"})

        if agent_type == "interviewer":
            return func(user_message, context)
        if agent_type == "evaluator":
            return func(user_message, context)
        return func(user_message)

    async def _real_chat(self, system_prompt: str, user_message: str) -> str:
        """Call the real LLM API."""
        if not self.api_key:
            raise RuntimeError(
                "API_KEY environment variable is required for real LLM mode. "
                "Set MODEL_PROVIDER=mock to use mock mode instead."
            )

        if self.provider in ("openai", "openrouter"):
            return await self._chat_openai_compatible(system_prompt, user_message)
        elif self.provider == "anthropic":
            return await self._chat_anthropic(system_prompt, user_message)
        else:
            raise ValueError(f"Unsupported MODEL_PROVIDER: {self.provider}")

    async def _chat_openai_compatible(self, system_prompt: str, user_message: str) -> str:
        """OpenAI-compatible API (works with OpenAI, OpenRouter, etc.)."""
        url = self.base_url or (
            "https://api.openai.com/v1/chat/completions"
            if self.provider == "openai"
            else "https://openrouter.ai/api/v1/chat/completions"
        )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        if self.provider == "openrouter":
            headers["HTTP-Referer"] = "http://localhost:8000"
            headers["X-Title"] = "AI Interview Training Agent"

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            "temperature": 0.3,
            "max_tokens": 4096,
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    async def _chat_anthropic(self, system_prompt: str, user_message: str) -> str:
        """Anthropic Messages API."""
        url = self.base_url or "https://api.anthropic.com/v1/messages"

        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
        }

        payload = {
            "model": self.model,
            "system": system_prompt,
            "messages": [
                {"role": "user", "content": user_message},
            ],
            "temperature": 0.3,
            "max_tokens": 4096,
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["content"][0]["text"]


# ── Singleton ────────────────────────────────────────────────────────

_llm_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client
