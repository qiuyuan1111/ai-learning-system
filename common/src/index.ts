/**
 * @ai-edu/common — 统一出口
 *
 * 所有对外公开的 DTO / 枚举 / 工具均从此文件再导出，
 * 调用方只需 `import { ... } from '@ai-edu/common'`，无需关心内部文件路径。
 */

// ───────── 枚举 ─────────
export {
  IntentEnum,
  type Intent,
} from './enums/IntentEnum'

export {
  ResourceTypeEnum,
  type ResourceType,
} from './enums/ResourceTypeEnum'

export {
  TaskStatusEnum,
  type TaskStatus,
} from './enums/TaskStatusEnum'

export {
  PathNodeStatusEnum,
  type PathNodeStatus,
} from './enums/PathNodeStatusEnum'

export {
  ErrorCodeEnum,
  type ErrorCode,
} from './enums/ErrorCodeEnum'

// ───────── 工具 ─────────
export { IdGenerator } from './utils/IdGenerator'
export { JsonUtils } from './utils/JsonUtils'

// ───────── 通用响应体 ─────────
export {
  type ApiResponse,
  success,
  error,
} from './dto/ApiResponse'

export {
  type PageInfo,
  type PaginatedData,
  paginated,
} from './dto/PageInfo'

// ───────── 会话 ─────────
export {
  type CreateSessionRequest,
  type CreateSessionResponse,
} from './dto/SessionDTO'

// ───────── 画像 ─────────
export {
  type UserProfile,
  type ProfileDimensions,
} from './dto/ProfileDTO'

// ───────── 资源 ─────────
export {
  type Resource,
  type GetResourcesParams,
  type GetResourcesResponse,
} from './dto/ResourceDTO'

// ───────── 任务 ─────────
export {
  type TaskInfo,
  type TaskProgressContent,
} from './dto/TaskDTO'

// ───────── 学习路径 ─────────
export {
  type PathNode,
  type LearningPathResponse,
} from './dto/PathDTO'

// ───────── 评估 ─────────
export {
  type SubmitEvaluationRequest,
  type AnswerItem,
  type BehaviorItem,
  type EvaluationReport,
  type EvaluationDimension,
  type WeakPoint,
} from './dto/EvaluationDTO'
