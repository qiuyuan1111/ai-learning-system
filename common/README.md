# 共享 DTO 与工具包 — AI Learning System

提供各智能体之间共享的数据模型、消息 DTO 和通用工具函数。

## 安装

```bash
# 在其他模块中引用（开发模式）
pip install -e ../common

# 或通过 requirements.txt 引用
# -e ../common
```

## 模块内容

- DTO 定义: WebSocket / REST 消息帧
- API 响应体: `ApiResponse` 通用信封
- 评估数据模型: `Answer`, `Behavior`, `EvaluationReport` 等

## 维护说明

> 由人员 C 维护，人员 A（网关）和人员 B（智能体）共同引用。
> 修改 DTO 需通知所有协作者同步更新。
