"""薄弱点发现服务

从错误答案和对话历史中提取薄弱知识点。

方法:
1. 统计错误题目的知识点标签
2. 分析对话中用户反复提问/表现出困惑的主题
3. 使用大模型对薄弱点进行归因分析
"""

import json
import logging
from typing import Dict, List

from ..config import settings
from ..models.evaluation import QuizResult, WeakPoint
from .llm_service import LLMService, LLMServiceError

logger = logging.getLogger(__name__)


class WeaknessFinder:
    """薄弱点发现器"""

    def __init__(self, llm_service: LLMService):
        self.llm = llm_service

    async def find(
        self,
        quiz_result: QuizResult,
        dialogue_history: List[Dict],
    ) -> List[WeakPoint]:
        """从答题结果和对话中提取薄弱点

        参数:
            quiz_result: 答题评分结果
            dialogue_history: 对话历史列表

        返回: 薄弱点列表，按严重程度降序排列
        """
        weak_points: List[WeakPoint] = []

        # 第 1 步：从错误知识点提取基础薄弱点
        weak_points.extend(self._from_wrong_topics(quiz_result))

        # 第 2 步：从对话中分析更深层的薄弱点
        dialogue_points = await self._from_dialogue(quiz_result, dialogue_history)
        weak_points.extend(dialogue_points)

        # 第 3 步：去重、排序、截断
        weak_points = self._deduplicate(weak_points)
        weak_points.sort(key=lambda w: w.severity, reverse=True)
        weak_points = weak_points[:settings.max_weak_points]

        return weak_points

    def _from_wrong_topics(self, quiz_result: QuizResult) -> List[WeakPoint]:
        """从错误题目知识点生成薄弱点

        相同知识点出现错误次数越多，严重程度越高。
        """
        from collections import Counter

        if not quiz_result.wrongTopics:
            return []

        topic_counts = Counter(quiz_result.wrongTopics)
        total_wrong = len(quiz_result.wrongTopics)

        points = []
        for topic, count in topic_counts.items():
            # 错误比例映射到严重度
            ratio = count / max(total_wrong, 1)
            severity = min(int(ratio * 5) + 1, 5)
            # 至少 2 分
            severity = max(severity, 2)

            points.append(WeakPoint(
                topic=topic,
                severity=severity,
                description=f"在「{topic}」相关题目中出现 {count} 次错误",
                suggestion=f"建议回顾「{topic}」的基础知识，完成相关练习",
            ))

        return points

    async def _from_dialogue(self, quiz_result: QuizResult, dialogue_history: List[Dict]) -> List[WeakPoint]:
        """从对话历史中分析薄弱点

        使用大模型从对话上下文挖掘更深层的薄弱环节。
        """
        if not dialogue_history:
            return []

        try:
            input_data = json.dumps({
                "wrongTopics": quiz_result.wrongTopics,
                "dialogue_history": dialogue_history[-10:],  # 最近 10 轮
            }, ensure_ascii=False)

            messages = [
                {"role": "system", "content": self._dialogue_prompt()},
                {"role": "user", "content": input_data},
            ]

            result = await self.llm.chat_structured(
                messages,
                temperature=0.4,
            )

            raw_points = result.get("weakPoints", [])
            if not isinstance(raw_points, list):
                return []
            return [
                WeakPoint(
                    topic=p.get("topic", "未知"),
                    severity=min(int(p.get("severity", 3)), 5),
                    description=p.get("description", ""),
                    suggestion=p.get("suggestion", ""),
                )
                for p in raw_points
                if p.get("topic") and int(p.get("severity", 0)) >= settings.weakness_severity_threshold
            ]
        except LLMServiceError as e:
            logger.warning("对话薄弱点分析失败: %s", e)
            return []

    def _deduplicate(self, points: List[WeakPoint]) -> List[WeakPoint]:
        """按 topic 去重，保留严重程度最高的"""
        seen: dict = {}
        for p in points:
            key = p.topic
            if key not in seen or p.severity > seen[key].severity:
                seen[key] = p
        return list(seen.values())

    @staticmethod
    def _dialogue_prompt() -> str:
        return """你是一位学习薄弱点分析专家。根据学生的答题错误知识点和对话历史，
分析学生的知识薄弱环节。

注意事项:
- 结合答题错误和对话上下文综合判断
- 识别学生反复困惑或表达困难的知识点
- 给出具体可行的改进建议

输出 JSON 格式:
{
  "weakPoints": [
    {
      "topic": "知识点名称",
      "severity": 1-5,  // 严重程度，5 为最严重
      "description": "具体问题描述",
      "suggestion": "改进建议"
    }
  ]
}

如果没有发现新的薄弱点，返回 {"weakPoints": []}。
"""
