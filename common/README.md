# @ai-edu/common

个性化学习多智能体系统 —— **共享库**。

集中维护全系统统一的 DTO（数据传输对象）、枚举、工具函数，
供前端、API 网关、各智能体微服务共同依赖，**避免接口字段定义散落各处、口径不一**。

> ⚠️ 本库的 DTO / 枚举 / 错误码即「对外接口契约」，对应 `docs/api.md`。
> 修改这些定义前请先与全员确认，改动需同步更新 `docs/api.md`。

---

## 目录结构

```
common/
├── src/
│   ├── index.ts              # 统一出口（前台总台）
│   ├── dto/                  # 数据传输对象（请求/响应规格）
│   │   ├── ApiResponse.ts    # 通用响应体 + success/error 构造器
│   │   ├── PageInfo.ts       # 分页信息 + paginated 构造器
│   │   ├── SessionDTO.ts     # 创建会话
│   │   ├── ProfileDTO.ts     # 用户画像（6 维度）
│   │   ├── ResourceDTO.ts    # 资源对象
│   │   ├── TaskDTO.ts        # 异步任务
│   │   ├── PathDTO.ts        # 学习路径节点
│   │   └── EvaluationDTO.ts  # 评估
│   ├── enums/                # 枚举（固定清单）
│   │   ├── IntentEnum.ts
│   │   ├── ResourceTypeEnum.ts
│   │   ├── TaskStatusEnum.ts
│   │   ├── PathNodeStatusEnum.ts
│   │   └── ErrorCodeEnum.ts
│   └── utils/                # 工具
│       ├── IdGenerator.ts    # 统一 ID 生成
│       └── JsonUtils.ts      # 安全 JSON 操作
├── dist/                     # 编译产物（自动生成，勿手改）
├── package.json
├── tsconfig.json
└── README.md
```

---

## 如何使用

### 1. 构建

```bash
cd common
npm install      # 安装 TypeScript 等开发依赖
npm run build    # 编译 src/ → dist/
```

### 2. 在其他服务中引用

**方式 A：本地软链（开发阶段推荐）**

```bash
# 在 common 目录执行一次
cd common && npm link

# 在需要使用的服务目录（如 gateway/、agents/xxx/）执行
cd <your-service>
npm link @ai-edu/common
```

之后即可在代码中直接使用：

```typescript
import {
  ApiResponse, success, error,
  Resource, TaskInfo, LearningPathResponse,
  ResourceTypeEnum, ErrorCodeEnum, TaskStatusEnum,
  IdGenerator,
} from '@ai-edu/common'

// 构造统一响应
const res: ApiResponse<Resource> = success({
  resourceId: IdGenerator.resourceId(),
  type: ResourceTypeEnum.PPT,
  title: 'BERT 模型讲解',
  url: 'https://cdn.xxx/bert.pptx',
  createdAt: new Date().toISOString(),
})

// 构造错误响应
const err = error(ErrorCodeEnum.TASK_NOT_FOUND, '任务不存在')
```

**方式 B：作为子目录直接引用**

若未发布到 npm，可在各服务的 `tsconfig.json` 中通过路径映射引用源码，
或直接将 `common/dist` 作为本地依赖。

---

## 导出内容速查

| 分类 | 名称 |
|------|------|
| 枚举 | `IntentEnum` / `Intent` |
|      | `ResourceTypeEnum` / `ResourceType` |
|      | `TaskStatusEnum` / `TaskStatus` |
|      | `PathNodeStatusEnum` / `PathNodeStatus` |
|      | `ErrorCodeEnum` / `ErrorCode` |
| 工具 | `IdGenerator`（sessionId / resourceId / taskId / pathId / requestId） |
|      | `JsonUtils`（safeParse / safeStringify / pretty / clone） |
| 响应 | `ApiResponse<T>` / `success` / `error` |
| 分页 | `PageInfo` / `PaginatedData<T>` / `paginated` |
| DTO  | `CreateSessionRequest` / `CreateSessionResponse` |
|      | `UserProfile` / `ProfileDimensions` |
|      | `Resource` / `GetResourcesParams` / `GetResourcesResponse` |
|      | `TaskInfo` / `TaskProgressContent` |
|      | `PathNode` / `LearningPathResponse` |
|      | `SubmitEvaluationRequest` / `AnswerItem` / `BehaviorItem` |
|      | `EvaluationReport` / `EvaluationDimension` / `WeakPoint` |

---

## 维护约定

- **契约稳定性**：DTO 字段名（camelCase）、枚举值、错误码数值与 `docs/api.md` 一一对应，修改需同步文档并通知全员。
- **版本管理**：每次破坏性变更（删字段、改类型）须递增 `package.json` 的主版本号并通知 A、B 升级。
- **构建产物**：`dist/` 为自动生成，请勿手动编辑或提交（已加入 `.gitignore`）。
