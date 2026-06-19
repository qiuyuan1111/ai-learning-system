## 5. 任务详解：评估智能体

### 5.1 项目结构

```
agents/evaluator/
├── src/
│   ├── main.py                 # FastAPI 入口 + REST 端点
│   ├── config.py
│   ├── models/
│   │   ├── evaluation.py       # 评估模型
│   │   └── dto.py              # 请求/响应 DTO
│   ├── services/
│   │   ├── evaluator.py        # 评估引擎核心
│   │   ├── quiz_grader.py      # 答题评分
│   │   ├── behavior_analyzer.py# 行为分析
│   │   ├── weakness_finder.py  # 薄弱点发现
│   │   └── llm_service.py      # 大模型调用
│   ├── prompts/
│   │   ├── grade.txt           # 评分提示词
│   │   └── analyze.txt         # 分析提示词
│   └── db/
│       └── repository.py
├── tests/
├── requirements.txt
└── Dockerfile
```

### 5.2 REST API 定义

#### 5.2.1 提交评估数据 — `POST /evaluation/submit`

```python
# main.py
from fastapi import FastAPI, HTTPException, Request
from models.dto import (
    ApiResponse,
    EvaluationSubmitRequest,
    EvaluationSubmitData,
    EvaluationReport,
    success,
    error,
)

app = FastAPI(title="评估智能体", version="1.0.0")


@app.post("/evaluation/submit", response_model=ApiResponse[EvaluationSubmitData])
async def submit_evaluation(req: EvaluationSubmitRequest, request: Request):
    """
    提交评估数据
    
    请求体（EvaluationSubmitRequest）:
    {
        "sessionId": "sess_abc",
        "quizId": "quiz_01",
        "answers": [
            { "questionId": "q1", "answer": "B", "timeSpent": 45 },
            { "questionId": "q2", "answer": "A", "timeSpent": 30 }
        ],
        "behaviors": [
            { "action": "video_pause", "resourceId": "res_001", "timestamp": "2026-06-15T10:00:00Z" }
        ]
    }
    
    成功响应（ApiResponse[EvaluationSubmitData]）:
    {
        "code": 0,
        "message": "success",
        "data": { "evaluationId": "eval_001", "status": "processing" },
        "requestId": "req_uuid"
    }

    失败响应:
    {
        "code": 1001,
        "message": "参数错误: sessionId 不能为空",
        "data": null,
        "requestId": "req_uuid"
    }
    """
    # 参数校验示例
    if not req.sessionId:
        return error(1001, "参数错误: sessionId 不能为空", request_id=str(request.headers.get("X-Request-Id", "")))
    
    # 处理评估...
    return success(
        EvaluationSubmitData(evaluationId="eval_001", status="processing"),
        request_id=str(request.headers.get("X-Request-Id", ""))
    )
```

#### 5.2.2 获取评估报告 — `GET /sessions/{sessionId}/evaluation-report`

```python
@app.get("/sessions/{sessionId}/evaluation-report", response_model=ApiResponse[EvaluationReport])
async def get_evaluation_report(sessionId: str, request: Request):
    """
    获取评估报告
    
    成功响应（ApiResponse[EvaluationReport]）:
    {
        "code": 0,
        "message": "success",
        "data": {
            "dimensions": [
                { "name": "基础知识掌握", "score": 85, "maxScore": 100 },
                { "name": "理解深度", "score": 70, "maxScore": 100 },
                { "name": "应用能力", "score": 60, "maxScore": 100 },
                { "name": "学习效率", "score": 90, "maxScore": 100 },
                { "name": "专注度", "score": 75, "maxScore": 100 }
            ],
            "weakPoints": [
                { "topic": "注意力机制", "severity": 4, "description": "对 Attention 的 Query/Key/Value 理解不够深入", "suggestion": "建议回顾 CS224n 第 6 讲" }
            ],
            "suggestions": [
                "建议回顾 CS224n 第 6 讲关于 Attention 的内容",
                "推荐完成「动手学深度学习」中反向传播的练习题"
            ],
            "pathAdjustments": [
                { "nodeId": "node_3", "action": "add", "title": "注意力机制专项练习" }
            ]
        },
        "requestId": "req_uuid"
    }

    会话不存在:
    {
        "code": 1002,
        "message": "会话不存在",
        "data": null,
        "requestId": "req_uuid"
    }
    """
    # 查询评估报告逻辑...
    report = await get_report_from_db(sessionId)
    if not report:
        raise HTTPException(status_code=404, detail=error(1002, "会话不存在"))
    return success(report, request_id=str(request.headers.get("X-Request-Id", "")))
```

### 5.3 核心服务方法

```python
# services/evaluator.py

class Evaluator:
    """
    评估引擎
    
    评估维度:
    1. 基础知识掌握 (knowledge_mastery) — 答题正确率
    2. 理解深度 (understanding_depth) — 复杂问题表现
    3. 应用能力 (application_ability) — 能否举一反三
    4. 学习效率 (learning_efficiency) — 单位时间掌握量
    5. 专注度 (engagement) — 行为数据反映的投入程度
    
    数据来源:
    - 答题数据: 正确率、用时
    - 行为数据: 视频暂停/快进/回放、资源浏览时长
    - 对话数据: 提问质量、追问深度
    """

    def __init__(self, llm_service, quiz_grader, behavior_analyzer, weakness_finder):
        self.llm = llm_service
        self.quiz_grader = quiz_grader
        self.behavior_analyzer = behavior_analyzer
        self.weakness_finder = weakness_finder

    async def evaluate(
        self,
        session_id: str,
        answers: List[Answer],
        behaviors: List[Behavior],
        dialogue_history: List[dict]
    ) -> EvaluationResult:
        """
        执行完整评估流程
        
        步骤:
        1. 答题评分 → 知识掌握度得分
        2. 行为分析 → 学习效率 + 专注度得分
        3. 对话分析 → 理解深度得分
        4. 薄弱点发现 → 从错误和对话中提取薄弱知识点
        5. 综合评分 → 各维度加权汇总
        6. 生成建议 → 基于薄弱点推荐改进方向
        7. 路径调整 → 建议需要加强的学习节点
        
        返回: EvaluationResult（包含维度评分、薄弱点、建议、路径调整）
        """
        # 第 1 步: 答题评分
        quiz_result = await self.quiz_grader.grade(answers)
        
        # 第 2 步: 行为分析
        behavior_score = await self.behavior_analyzer.analyze(behaviors)
        
        # 第 3 步: 薄弱点发现
        weak_points = await self.weakness_finder.find(
            quiz_result=quiz_result,
            dialogue_history=dialogue_history
        )
        
        # 第 4 步: 大模型综合评估
        evaluation = await self.llm.generate_evaluation(
            quiz_result=quiz_result,
            behavior_score=behavior_score,
            weak_points=weak_points,
            profile=await self.profile_service.get_profile(session_id)
        )
        
        return evaluation


# services/quiz_grader.py

class QuizGrader:
    """
    答题评分器
    
    支持多种题型评分:
    - 选择题: 直接对比答案
    - 填空题: 关键词匹配 + 语义相似度
    - 简答题: 大模型评分（根据参考答案和评分标准）
    """

    async def grade(self, answers: List[Answer]) -> QuizResult:
        """
        评分逻辑:
        1. 选择题: answer === correct_answer → 正确，否则错误
        2. 简答题: 调用大模型，传入"问题 + 参考答案 + 学生答案" → 返回分数
        
        返回:
        {
            "totalScore": 85,
            "maxScore": 100,
            "details": [
                { "questionId": "q1", "score": 10, "maxScore": 10, "correct": true },
                { "questionId": "q2", "score": 7, "maxScore": 10, "correct": false }
            ],
            "wrongTopics": ["反向传播", "损失函数"]
        }
        """
        pass


# services/weakness_finder.py

class WeaknessFinder:
    """
    薄弱点发现器
    
    从错误答案和对话历史中提取薄弱知识点。
    
    方法:
    1. 统计错误题目的知识点标签
    2. 分析对话中用户反复提问/表现出困惑的主题
    3. 使用大模型对薄弱点进行归因分析
    """

    async def find(
        self,
        quiz_result: QuizResult,
        dialogue_history: List[dict]
    ) -> List[WeakPoint]:
        """
        返回薄弱点列表，每个薄弱点包含:
        - topic: 知识点名称
        - severity: 严重程度 (1-5)
        - description: 具体问题描述
        - suggestion: 改进建议
        """
        pass
```

---
