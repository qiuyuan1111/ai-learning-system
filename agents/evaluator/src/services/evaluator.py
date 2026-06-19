"""评估引擎核心

执行完整评估流程:
1. 答题评分 → 知识掌握度得分
2. 行为分析 → 学习效率 + 专注度得分
3. 对话分析 → 理解深度得分
4. 薄弱点发现 → 从错误和对话中提取薄弱知识点
5. 综合评分 → 各维度加权汇总
6. 生成建议 → 基于薄弱点推荐改进方向
7. 路径调整 → 建议需要加强的学习节点
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional

from ..config import settings
from ..models.evaluation import (
    Answer,
    Behavior,
    DimensionScore,
    EvaluationResult,
    PathAdjustment,
    WeakPoint,
)
from .behavior_analyzer import BehaviorAnalyzer
from .llm_service import LLMService, LLMServiceError
from .profile_service_client import ProfileServiceClient
from .quiz_grader import QuizGrader
from .weakness_finder import WeaknessFinder

logger = logging.getLogger(__name__)

# 综合评估提示词模板路径
_ANALYZE_PROMPT_FILE = os.path.join(os.path.dirname(__file__), "..", "prompts", "analyze.txt")


class Evaluator:
    """评估引擎

    评估维度:
    1. knowledge_mastery（基础知识掌握）— 答题正确率
    2. understanding_depth（理解深度）— 复杂问题表现
    3. application_ability（应用能力）— 能否举一反三
    4. learning_efficiency（学习效率）— 单位时间掌握量
    5. engagement（专注度）— 行为数据反映的投入程度

    数据来源:
    - 答题数据: 正确率、用时
    - 行为数据: 视频暂停/快进/回放、资源浏览时长
    - 对话数据: 提问质量、追问深度
    """

    def __init__(
        self,
        llm_service: LLMService,
        quiz_grader: QuizGrader,
        behavior_analyzer: BehaviorAnalyzer,
        weakness_finder: WeaknessFinder,
        profile_service: ProfileServiceClient,
    ):
        self.llm = llm_service
        self.quiz_grader = quiz_grader
        self.behavior_analyzer = behavior_analyzer
        self.weakness_finder = weakness_finder
        self.profile_service = profile_service
        self._analyze_prompt: str = ""

    async def evaluate(
        self,
        session_id: str,
        answers: List[Answer],
        behaviors: List[Behavior],
        dialogue_history: List[Dict],
    ) -> EvaluationResult:
        """执行完整评估流程

        步骤:
        1. 答题评分 → 知识掌握度得分
        2. 行为分析 → 学习效率 + 专注度得分
        3. 薄弱点发现 → 从错误和对话中提取薄弱知识点
        4. 获取用户画像（可选）
        5. 大模型综合评估 → 各维度评分 + 建议 + 路径调整

        返回: EvaluationResult（包含维度评分、薄弱点、建议、路径调整）
        """
        logger.info("开始评估 session=%s", session_id)

        # 第 1 步: 答题评分
        quiz_result = await self.quiz_grader.grade(answers)
        logger.info("答题评分完成: %.1f/%.1f", quiz_result.totalScore, quiz_result.maxScore)

        # 第 2 步: 行为分析
        behavior_score = await self.behavior_analyzer.analyze(behaviors)
        logger.info(
            "行为分析完成: efficiency=%.2f, engagement=%.2f",
            behavior_score.learningEfficiency,
            behavior_score.engagement,
        )

        # 第 3 步: 薄弱点发现
        weak_points = await self.weakness_finder.find(
            quiz_result=quiz_result,
            dialogue_history=dialogue_history,
        )
        logger.info("薄弱点发现完成: %d 个", len(weak_points))

        # 第 4 步: 获取用户画像（可选，失败不影响评估）
        profile = None
        try:
            profile = await self.profile_service.get_profile(session_id)
        except Exception as e:
            logger.warning("获取画像失败，使用默认值: %s", e)

        # 第 5 步: 大模型综合评估
        evaluation = await self._generate_comprehensive_evaluation(
            quiz_result=quiz_result,
            behavior_score=behavior_score,
            weak_points=weak_points,
            profile=profile,
        )

        # 补充 sessionId 和时间
        evaluation.sessionId = session_id

        logger.info("评估完成 session=%s", session_id)
        return evaluation

    async def _generate_comprehensive_evaluation(
        self,
        quiz_result: Any,
        behavior_score: Any,
        weak_points: List[WeakPoint],
        profile: Optional[Dict[str, Any]],
    ) -> EvaluationResult:
        """调用大模型生成综合评估

        将各子服务的结果汇总，让大模型进行综合判断。
        包含降级逻辑：大模型调用失败时使用规则计算。
        """
        try:
            result = await self._call_llm_evaluation(
                quiz_result, behavior_score, weak_points, profile,
            )
            return self._parse_llm_result(result)
        except LLMServiceError as e:
            logger.warning("大模型综合评估失败，使用规则评估: %s", e)
            return self._rule_based_evaluation(quiz_result, behavior_score, weak_points)

    async def _call_llm_evaluation(
        self,
        quiz_result: Any,
        behavior_score: Any,
        weak_points: List[WeakPoint],
        profile: Optional[Dict[str, Any]],
    ) -> dict:
        """调用大模型进行综合评估"""
        self._ensure_analyze_prompt()

        input_data = json.dumps({
            "quizResult": {
                "totalScore": quiz_result.totalScore,
                "maxScore": quiz_result.maxScore,
                "wrongTopics": quiz_result.wrongTopics,
            },
            "behaviorScore": {
                "learningEfficiency": behavior_score.learningEfficiency,
                "engagement": behavior_score.engagement,
                "details": behavior_score.details,
            },
            "weakPoints": [w.model_dump() for w in weak_points],
            "profile": profile or {},
        }, ensure_ascii=False)

        messages = [
            {"role": "system", "content": self._analyze_prompt},
            {"role": "user", "content": input_data},
        ]

        return await self.llm.chat_structured(messages, temperature=0.4)

    def _parse_llm_result(self, raw: dict) -> EvaluationResult:
        """将大模型返回的 JSON 解析为 EvaluationResult"""
        dimensions = [
            DimensionScore(
                name=d.get("name", ""),
                score=float(d.get("score", 0)),
                maxScore=float(d.get("maxScore", 100)),
            )
            for d in raw.get("dimensions", [])
            if d.get("name")
        ]

        weak_points = [
            WeakPoint(
                topic=w.get("topic", ""),
                severity=int(w.get("severity", 3)),
                description=w.get("description", ""),
                suggestion=w.get("suggestion", ""),
            )
            for w in raw.get("weakPoints", [])
            if w.get("topic")
        ]

        suggestions = raw.get("suggestions", [])

        path_adjustments = [
            PathAdjustment(
                nodeId=p.get("nodeId", ""),
                action=p.get("action", "add"),
                title=p.get("title", ""),
            )
            for p in raw.get("pathAdjustments", [])
            if p.get("nodeId")
        ]

        return EvaluationResult(
            sessionId="",
            dimensions=dimensions,
            weakPoints=weak_points,
            suggestions=suggestions,
            pathAdjustments=path_adjustments,
        )

    def _rule_based_evaluation(
        self,
        quiz_result: Any,
        behavior_score: Any,
        weak_points: List[WeakPoint],
    ) -> EvaluationResult:
        """大模型不可用时的规则兜底评估"""
        # 计算知识掌握度
        knowledge_mastery = 0.0
        if quiz_result.maxScore > 0:
            knowledge_mastery = quiz_result.totalScore / quiz_result.maxScore

        # 理解深度：基于高难度题目表现
        understanding_depth = self._calc_understanding_depth(quiz_result)

        # 应用能力：基于应用题表现
        application_ability = self._calc_application_ability(quiz_result)

        # 学习效率和专注度从行为分析直接取
        learning_efficiency = behavior_score.learningEfficiency
        engagement = behavior_score.engagement

        dimensions = [
            DimensionScore(name="knowledge_mastery", score=round(knowledge_mastery * 100, 1)),
            DimensionScore(name="understanding_depth", score=round(understanding_depth * 100, 1)),
            DimensionScore(name="application_ability", score=round(application_ability * 100, 1)),
            DimensionScore(name="learning_efficiency", score=round(learning_efficiency * 100, 1)),
            DimensionScore(name="engagement", score=round(engagement * 100, 1)),
        ]

        # 生成建议
        suggestions = self._generate_suggestions(weak_points)

        # 生成路径调整
        path_adjustments = self._generate_path_adjustments(weak_points)

        return EvaluationResult(
            sessionId="",
            dimensions=dimensions,
            weakPoints=weak_points,
            suggestions=suggestions,
            pathAdjustments=path_adjustments,
        )

    def _calc_understanding_depth(self, quiz_result: Any) -> float:
        """从高难度题目计算理解深度（难度 >= 7 的题目的正确率）"""
        hard_correct = 0
        hard_total = 0
        for d in quiz_result.details:
            difficulty = d.get("difficulty", 5)
            if isinstance(difficulty, (int, float)) and difficulty >= 7:
                hard_total += 1
                if d.get("correct", False):
                    hard_correct += 1

        if hard_total == 0:
            return 0.5  # 无高难度题，使用默认值
        return hard_correct / hard_total

    def _calc_application_ability(self, quiz_result: Any) -> float:
        """从应用题计算应用能力"""
        app_correct = 0
        app_total = 0
        for d in quiz_result.details:
            if d.get("questionType") == "essay":
                app_total += 1
                score = d.get("score", 0)
                max_score = d.get("maxScore", 10)
                if max_score > 0 and score / max_score >= 0.7:
                    app_correct += 1

        if app_total == 0:
            return 0.5
        return app_correct / app_total

    def _generate_suggestions(self, weak_points: List[WeakPoint]) -> List[str]:
        """基于薄弱点生成建议"""
        suggestions = []
        for w in weak_points:
            if w.suggestion:
                suggestions.append(w.suggestion)
        if not suggestions:
            suggestions.append("当前未发现明显薄弱点，建议继续保持当前学习节奏")
        return suggestions

    def _generate_path_adjustments(self, weak_points: List[WeakPoint]) -> List[PathAdjustment]:
        """基于薄弱点生成路径调整建议"""
        adjustments = []
        for i, w in enumerate(weak_points[:3]):
            if w.severity >= 4:
                adjustments.append(PathAdjustment(
                    nodeId=f"weakness_{i}",
                    action="add",
                    title=f"{w.topic}专项练习",
                ))
        return adjustments

    def _ensure_analyze_prompt(self) -> None:
        """加载综合评估提示词模板（带缓存）"""
        if self._analyze_prompt:
            return
        try:
            with open(_ANALYZE_PROMPT_FILE, encoding="utf-8") as f:
                self._analyze_prompt = f.read()
        except FileNotFoundError:
            self._analyze_prompt = _DEFAULT_ANALYZE_PROMPT


_DEFAULT_ANALYZE_PROMPT = """你是一位专业的学习评估分析师。综合学生的答题数据、行为数据和对话历史，进行多维度评估。

评估维度:
1. knowledge_mastery（基础知识掌握）— 答题正确率反映的基础知识牢固程度
2. understanding_depth（理解深度）— 对复杂问题和概念的深层理解
3. application_ability（应用能力）— 能否将知识应用于新场景
4. learning_efficiency（学习效率）— 单位时间内掌握的知识量
5. engagement（专注度）— 学习过程中的投入程度

请基于输入数据，输出 JSON 格式的评估结果：
{
  "dimensions": [
    { "name": "knowledge_mastery", "score": 0-100, "maxScore": 100 },
    { "name": "understanding_depth", "score": 0-100, "maxScore": 100 },
    { "name": "application_ability", "score": 0-100, "maxScore": 100 },
    { "name": "learning_efficiency", "score": 0-100, "maxScore": 100 },
    { "name": "engagement", "score": 0-100, "maxScore": 100 }
  ],
  "weakPoints": [
    { "topic": "薄弱知识点", "severity": 1-5, "description": "具体问题描述", "suggestion": "改进建议" }
  ],
  "suggestions": ["建议1", "建议2"],
  "pathAdjustments": [
    { "nodeId": "node_id", "action": "add|remove|reorder", "title": "节点标题" }
  ]
}
"""
