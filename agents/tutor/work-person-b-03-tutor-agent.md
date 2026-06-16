## 4. 任务详解：辅导智能体

### 4.1 项目结构

```
agents/tutor/
├── src/
│   ├── main.py                 # FastAPI 入口 + WebSocket 端点
│   ├── config.py               # 配置
│   ├── models/
│   │   ├── context.py          # 对话上下文模型
│   │   └── dto.py              # 消息 DTO
│   ├── services/
│   │   ├── tutor_engine.py     # 辅导引擎核心
│   │   ├── answer_generator.py # 答案生成（含画像适配）
│   │   ├── context_manager.py  # 对话上下文管理
│   │   └── llm_service.py      # 大模型调用（同画像智能体模式）
│   ├── prompts/
│   │   ├── system.txt          # 系统提示词（角色设定）
│   │   └── adapt.txt           # 画像适配提示词
│   ├── db/
│   │   └── chat_history.py     # 对话历史存储
│   └── ws/
│       └── handler.py          # WebSocket 消息处理器
├── tests/
│   ├── test_tutor_engine.py
│   └── test_answer_generator.py
├── requirements.txt
└── Dockerfile
```

### 4.2 核心服务方法

```python
# services/tutor_engine.py

class TutorEngine:
    """
    辅导引擎
    
    职责：
    接收用户的辅导请求（intent=tutoring），结合画像生成个性化回答。
    支持多模态输入（图片/附件），输出图文混合 Markdown。
    
    核心策略：
    1. 根据画像中的 knowledge_base 调整回答深度
    2. 根据 cognitive_style 调整呈现方式（理论推导 / 代码示例 / 图解）
    3. 根据 learning_pace 调整语速和信息密度
    4. 关联 weakness_preferences 对薄弱点着重讲解
    5. 关联 interest_areas 使用用户感兴趣的例子
    """

    def __init__(self, llm_service, profile_service):
        self.llm = llm_service
        self.profile_service = profile_service

    async def generate_answer(
        self,
        session_id: str,
        question: str,
        attachments: List[dict],
        context: dict
    ) -> AsyncGenerator[dict, None]:
        """
        生成个性化辅导回答
        
        参数:
            session_id: 会话 ID（用于获取画像）
            question: 用户问题
            attachments: 附件列表（图片等）
            context: 上下文（resourceId, courseId 等）
        
        生成（yield）:
            逐步输出 type=text 流式消息
            最终输出 type=done 结束
        
        实现步骤:
        1. 从 profile_service 获取当前画像
        2. 根据画像构建系统提示词（注入画像维度信息）
        3. 从 context_manager 获取对话历史
        4. 调用 llm.chat_stream() 生成回答
        5. 将回答通过 WS 逐段推送给前端
        """
        # 1. 获取画像
        profile = await self.profile_service.get_profile(session_id)
        
        # 2. 构建系统提示词
        system_prompt = self._build_system_prompt(profile, context)
        
        # 3. 构建消息列表
        messages = self._build_messages(system_prompt, question, attachments)
        
        # 4. 流式生成
        async for chunk in self.llm.chat_stream(messages):
            yield {
                "type": "text",
                "content": {"markdown": chunk}
            }
        
        # 5. 结束
        yield {"type": "done", "content": {}}

    def _build_system_prompt(self, profile: UserProfile, context: dict) -> str:
        """
        根据画像和上下文构建系统提示词
        
        例如:
        - 用户知识水平=intermediate → "使用中等难度的术语解释"
        - 认知风格=practical → "多提供代码示例和实际应用场景"
        - 薄弱点包含"注意力机制" → "对注意力机制部分重点讲解"
        """
        pass

    def _build_messages(
        self,
        system_prompt: str,
        question: str,
        attachments: List[dict]
    ) -> List[dict]:
        """
        构建大模型消息列表
        
        如果有图片附件，根据模型能力选择:
        - 支持多模态 → 直接传入 image_url
        - 不支持 → 先使用图片描述模型生成文本描述再传入
        """
        pass


# services/context_manager.py

class ContextManager:
    """
    对话上下文管理器
    
    职责：
    维护多轮对话历史，支持上下文窗口截断。
    当对话过长时，自动摘要历史或丢弃最早轮次。
    
    策略:
    - 保留最近 10 轮完整对话
    - 超过 10 轮时，将前文压缩为摘要
    - 每次请求携带最近 N 轮 + 摘要
    """

    MAX_ROUNDS = 10

    async def get_context(self, session_id: str) -> List[dict]:
        """获取当前会话的对话上下文"""
        pass

    async def append_round(self, session_id: str, question: str, answer: str):
        """追加一轮对话记录"""
        pass

    async def summarize_history(self, session_id: str) -> str:
        """对历史对话进行摘要"""
        pass
```

---
