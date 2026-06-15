## 6. 任务详解：内容安全与防幻觉模块

### 6.1 内容安全过滤器

```python
# 位置: 可作为独立模块 agents/safety/ 或集成到各智能体中
# 建议作为独立服务，所有智能体统一调用

class ContentSafetyFilter:
    """
    内容安全过滤器
    
    职责：
    对 AI 生成内容进行安全审核，拦截违规内容。
    
    实现方式:
    1. 关键词过滤 — 敏感词库匹配
    2. 大模型审核 — 调用 OpenAI  moderation API
    3. 规则引擎 — 特定模式的拦截规则
    
    触发时机:
    每次智能体生成最终答案前，调用本过滤器
    命中违规 → 返回 code 3001, 推送友好提示
    """

    SENSITIVE_KEYWORDS = [...]  # 敏感词库

    async def check(self, text: str) -> SafetyVerdict:
        """
        审核文本内容
        
        返回:
        {
            "passed": True/False,         # 是否通过审核
            "riskLevel": "safe|suspect|violation",
            "violatedRules": ["规则1", "规则2"],
            "suggestion": "建议修改..."
        }
        """
        # 1. 关键词匹配
        # 2. 大模型审核
        pass
```

### 6.2 防幻觉校验模块

```python
class HallucinationGuard:
    """
    防幻觉校验模块
    
    职责：
    检查模型生成内容是否存在"幻觉"（无根据的虚假信息）。
    
    实现方式:
    1. 引用核查 — 检查引用的论文/资源是否存在
    2. 事实一致性 — 与已知事实对比
    3. 置信度评估 — 对不确定内容进行标注
    
    触发时机:
    资源生成、辅导回答输出前
    命中幻觉 → 返回 code 3002, 推送"暂无法提供准确答案"
    """

    async def check(self, generated_text: str, context: dict) -> HallucinationVerdict:
        """
        校验是否存在幻觉
        
        context 包含:
        - profile: 用户画像（知识水平）
        - source_material: 参考来源（如有）
        - dialogue_history: 对话历史
        
        返回:
        {
            "passed": True/False,
            "hallucinatedClaims": [
                {"claim": "XXX论文证明了...", "evidence": "未找到该论文", "confidence": 0.1}
            ],
            "overallConfidence": 0.85
        }
        
        策略:
        - 如果 generated_text 引用了具体论文/数据/事实:
          → 使用大模型判断该引用是否可能为真实
          → 低置信度引用标记为"疑似幻觉"
        - 对于学术资源生成:
          → 强制要求标注参考来源
          → 无来源标注的内容要求重新生成
        """
        pass
```

---
