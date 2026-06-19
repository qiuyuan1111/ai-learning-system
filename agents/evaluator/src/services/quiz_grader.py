"""答题评分服务

支持多种题型评分:
- 选择题（choice）：直接对比答案
- 填空题（fill）：关键词匹配 + 大模型语义相似度
- 简答题（essay）：大模型评分（根据参考答案和评分标准）
"""

import json
import logging
import os
from typing import List

from ..config import settings
from ..models.evaluation import Answer, QuizResult
from .llm_service import LLMService, LLMServiceError

logger = logging.getLogger(__name__)

# 评分提示词模板路径
_PROMPT_FILE = os.path.join(os.path.dirname(__file__), "..", "prompts", "grade.txt")


class QuizGrader:
    """答题评分器"""

    def __init__(self, llm_service: LLMService):
        self.llm = llm_service
        self._system_prompt: str = ""

    async def grade(self, answers: List[Answer]) -> QuizResult:
        """对一批答题进行评分

        评分逻辑:
        1. 选择题: answer === correctAnswer → 正确，否则错误
        2. 填空题/简答题: 调用大模型，传入"问题 + 参考答案 + 学生答案" → 返回分数

        返回: QuizResult（包含总分、明细、错误知识点）
        """
        if not answers:
            return QuizResult()

        self._ensure_system_prompt()

        details = []
        total_score = 0.0
        max_score = 0.0
        wrong_topics: List[str] = []

        for ans in answers:
            result = await self._grade_single(ans)
            details.append(result)

            score = result.get("score", 0)
            max_s = result.get("maxScore", 10)
            total_score += score
            max_score += max_s

            if not result.get("correct", False):
                for t in result.get("wrongTopics", []):
                    if t and t not in wrong_topics:
                        wrong_topics.append(t)

        return QuizResult(
            totalScore=total_score,
            maxScore=max_score,
            details=details,
            wrongTopics=wrong_topics,
        )

    async def _grade_single(self, ans: Answer) -> dict:
        """单题评分

        选择题直接比对，主观题调用大模型。
        """
        if ans.questionType == "choice":
            return self._grade_choice(ans)
        return await self._grade_llm(ans)

    def _grade_choice(self, ans: Answer) -> dict:
        """选择题直接对比答案"""
        correct = ans.answer.strip().upper() == (ans.correctAnswer or "").strip().upper()
        max_score = max(5, ans.difficulty * 2) if ans.difficulty else 10.0
        return {
            "questionId": ans.questionId,
            "score": max_score if correct else 0.0,
            "maxScore": max_score,
            "correct": correct,
            "difficulty": ans.difficulty,
            "questionType": ans.questionType,
            "analysis": "正确" if correct else "错误",
            "wrongTopics": [] if correct else [ans.topic] if ans.topic else [],
        }

    async def _grade_llm(self, ans: Answer) -> dict:
        """主观题调用大模型评分"""
        try:
            input_data = json.dumps({
                "question": f"题目 {ans.questionId}",
                "type": ans.questionType,
                "topic": ans.topic,
                "difficulty": ans.difficulty,
                "correctAnswer": ans.correctAnswer or "",
                "studentAnswer": ans.answer,
                "timeSpent": ans.timeSpent,
                "maxScore": 10,
            }, ensure_ascii=False)

            messages = [
                {"role": "system", "content": self._system_prompt},
                {"role": "user", "content": input_data},
            ]

            result = await self.llm.chat_structured(
                messages,
                temperature=0.3,  # 评分使用较低温度保证一致性
            )
            result["questionId"] = ans.questionId
            result["difficulty"] = ans.difficulty
            result["questionType"] = ans.questionType
            return result
        except LLMServiceError as e:
            logger.warning("大模型评分失败，使用默认评分: %s", e)
            return {
                "questionId": ans.questionId,
                "score": 0.0,
                "maxScore": 10.0,
                "correct": False,
                "difficulty": ans.difficulty,
                "questionType": ans.questionType,
                "analysis": "评分异常，默认 0 分",
                "wrongTopics": [ans.topic] if ans.topic else [],
            }

    def _ensure_system_prompt(self) -> None:
        """加载评分提示词模板（带缓存）"""
        if self._system_prompt:
            return
        try:
            with open(_PROMPT_FILE, encoding="utf-8") as f:
                self._system_prompt = f.read()
        except FileNotFoundError:
            self._system_prompt = _DEFAULT_GRADE_PROMPT


_DEFAULT_GRADE_PROMPT = """你是一位严谨的课程评估评分助手。根据参考答案和学生回答进行评分。

评分规则:
- 选择题（choice）：答案完全一致 → 满分，不一致 → 0 分
- 填空题（fill）：允许同义词和合理表述，按正确率（0-100%）评分
- 简答题（essay）：根据参考答案综合评分（0-100%）

输入格式:
{
  "question": "题目原文",
  "type": "choice | fill | essay",
  "topic": "关联知识点",
  "difficulty": 1-10,
  "correctAnswer": "参考答案",
  "studentAnswer": "学生答案",
  "timeSpent": 45,
  "maxScore": 10
}

输出格式:
{
  "score": 8.5,
  "maxScore": 10,
  "correct": true,
  "analysis": "简要说明得分理由",
  "wrongTopics": ["知识点1"]
}
"""
