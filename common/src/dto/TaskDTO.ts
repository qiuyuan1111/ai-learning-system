import type { TaskStatus } from '../enums/TaskStatusEnum'
import type { Resource } from './ResourceDTO'

/**
 * 异步任务定义（见 work-person-c.md 3.2.5）
 *
 * 资源生成等耗时操作采用异步任务模式，
 * 客户端轮询 GET /resource-tasks/{taskId} 获取最新状态。
 */
export interface TaskInfo {
  taskId: string
  status: TaskStatus
  /** 进度百分比 0-100 */
  progress: number
  /** 进度描述文字 */
  progressDescription?: string
  /** 任务完成后返回的资源列表 */
  result?: {
    resources: Resource[]
  }
  /** 任务失败时的错误信息 */
  error?: {
    code: number
    message: string
  }
  /** 创建时间（ISO8601） */
  createdAt: string
  /** 更新时间（ISO8601） */
  updatedAt: string
}

/**
 * WS 推送的任务进度消息 content 部分（type=progress，见 api.md 2.2）
 */
export interface TaskProgressContent {
  taskId: string
  progress: number
  description: string
}
