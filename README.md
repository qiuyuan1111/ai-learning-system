# AI Learning System — 智能教育系统

基于大语言模型的个性化学习辅导系统，通过画像构建、智能辅导和评估反馈三个核心智能体，为用户提供自适应学习体验。

## 系统架构

```
┌─────────────────────────────────────────────────────┐
│                     API 网关 (人员 A)                  │
│          WebSocket (chat)  +  REST (evaluation)       │
└──────────┬──────────┬──────────┬──────────────────────┘
           │          │          │
     ┌─────▼──┐ ┌────▼───┐ ┌───▼──────┐
     │ 画像    │ │ 辅导    │ │ 评估      │
     │ 智能体  │ │ 智能体  │ │ 智能体    │
     │ Profile│ │ Tutor  │ │ Evaluator│
     └────┬────┘ └───┬────┘ └────┬─────┘
          │          │           │
          └──────────┼───────────┘
                     ▼
             ┌───────────────┐
             │  共享 DTO +    │
             │  安全过滤模块   │
             └───────────────┘
```

## 模块说明

| 模块 | 职责 | 通信方式 | 端口 |
|------|------|---------|------|
| **agents/profile/** | 用户画像构建与增量更新 | WebSocket | 8081 |
| **agents/tutor/** | 个性化答疑与辅导 | WebSocket | 8082 |
| **agents/evaluator/** | 学习评估与薄弱点分析 | REST | 8080 |
| **agents/safety/** | 内容安全审核与防幻觉 | REST(内部) | 8083 |

## 技术栈

- **语言:** Python 3.11+
- **框架:** FastAPI + Pydantic v2
- **大模型:** OpenAI API (GPT-4o / GPT-4o-mini)
- **通信:** WebSocket + REST
- **存储:** 待定 (ChromaDB / PostgreSQL)
- **测试:** pytest

## 快速开始

```bash
# 克隆仓库
git clone https://github.com/qiuyuan1111/ai-learning-system.git
cd ai-learning-system

# 安装依赖 (以画像智能体为例)
cd agents/profile
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入你的 OPENAI_API_KEY

# 启动服务
python src/main.py
```

## 分支策略

```
main          ← 生产就绪版本
  └─ develop  ← 集成开发分支
       ├─ feature/agent-profile    ← 画像智能体
       ├─ feature/agent-tutor      ← 辅导智能体
       ├─ feature/agent-evaluator  ← 评估智能体
       └─ feature/agent-safety     ← 安全模块
```

## 文档

各模块详细规范见对应目录下的 `.md` 文件：

- [`agents/profile/work-person-b-02-profile-agent.md`](agents/profile/work-person-b-02-profile-agent.md)
- [`agents/tutor/work-person-b-03-tutor-agent.md`](agents/tutor/work-person-b-03-tutor-agent.md)
- [`agents/evaluator/work-person-b-04-evaluator-agent.md`](agents/evaluator/work-person-b-04-evaluator-agent.md)
- [`agents/safety/work-person-b-05-safety-guard.md`](agents/safety/work-person-b-05-safety-guard.md)
- [`common/work-person-b-06-core-dto.md`](common/work-person-b-06-core-dto.md)

## 许可

MIT License
