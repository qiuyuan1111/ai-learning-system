"""行为分析服务

从用户学习行为数据中分析学习效率和专注度。

行为分析维度:
1. 学习效率（learning_efficiency）— 基于答题用时、视频观看模式、资源访问频率
2. 专注度（engagement）— 基于视频暂停/快进/回放模式、学习时长分布
"""

import logging
from typing import List

from ..models.evaluation import Behavior, BehaviorScore

logger = logging.getLogger(__name__)


class BehaviorAnalyzer:
    """行为分析器

    分析用户学习行为数据，输出学习效率和专注度得分。
    """

    async def analyze(self, behaviors: List[Behavior]) -> BehaviorScore:
        """分析行为数据

        从行为中提取模式并计算评分:
        - 学习效率: 视频操作合理度、答题速度适中度
        - 专注度: 暂停频率、快进退、学习连续性

        返回: BehaviorScore（包含 learningEfficiency 和 engagement）
        """
        if not behaviors:
            return BehaviorScore()

        # 统计各类行为计数
        pauses = [b for b in behaviors if b.action == "video_pause"]
        seeks_forward = [b for b in behaviors if b.action == "video_seek_forward"]
        seeks_back = [b for b in behaviors if b.action == "video_seek_back"]
        resource_views = [b for b in behaviors if b.action == "resource_view"]

        # 计算学习效率分
        efficiency = self._calc_efficiency(behaviors, seeks_forward, seeks_back)

        # 计算专注度
        engagement = self._calc_engagement(behaviors, pauses, resource_views)

        return BehaviorScore(
            learningEfficiency=round(efficiency, 2),
            engagement=round(engagement, 2),
            details={
                "totalActions": len(behaviors),
                "pauseCount": len(pauses),
                "seekForwardCount": len(seeks_forward),
                "seekBackCount": len(seeks_back),
                "resourceViewCount": len(resource_views),
            },
        )

    def _calc_efficiency(self, all_behaviors: List[Behavior], seeks_forward: List[Behavior], seeks_back: List[Behavior]) -> float:
        """计算学习效率

        原则:
        - 适当回放（seek_back）说明在主动复习，效率加分
        - 频繁快进（seek_forward）说明可能走马观花，效率扣分
        - 行为总量适中效率高，过少或过多都偏低
        """
        total = len(all_behaviors)
        if total == 0:
            return 0.5

        # 基础分
        score = 0.7

        # 回放加分（适度回放表示积极学习）
        back_ratio = len(seeks_back) / total
        score += min(back_ratio * 2, 0.2)

        # 快进扣分
        forward_ratio = len(seeks_forward) / total
        score -= min(forward_ratio * 2, 0.2)

        # 行为总量偏离惩罚
        if total < 3:
            score -= 0.1  # 行为太少，信心不足
        elif total > 50:
            score -= 0.1  # 行为过多，可能注意力分散

        return max(0.0, min(1.0, score))

    def _calc_engagement(self, all_behaviors: List[Behavior], pauses: List[Behavior], resource_views: List[Behavior]) -> float:
        """计算专注度

        原则:
        - 暂停学习（结合 pause 和 resource_view）说明在认真思考，专注加分
        - 频繁无故暂停则扣分
        - 资源查看说明主动拓展学习，专注加分
        """
        total = len(all_behaviors)
        if total == 0:
            return 0.5

        score = 0.7

        # 暂停分析：适度暂停说明在思考
        pause_ratio = len(pauses) / total
        if pause_ratio <= 0.3:
            score += 0.1
        elif pause_ratio > 0.6:
            score -= 0.15  # 暂停过多可能注意力不集中

        # 资源查看加分
        resource_ratio = len(resource_views) / total
        score += min(resource_ratio * 1.5, 0.15)

        # 快进退的极端值扣分
        seeks = [b for b in all_behaviors if b.action in ("video_seek_forward", "video_seek_back")]
        seek_ratio = len(seeks) / total
        if seek_ratio > 0.4:
            score -= 0.1

        return max(0.0, min(1.0, score))
