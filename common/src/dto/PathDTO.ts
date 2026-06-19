import type { ResourceType } from '../enums/ResourceTypeEnum'
import type { PathNodeStatus } from '../enums/PathNodeStatusEnum'

/**
 * 学习路径节点（见 work-person-c.md 3.2.6）
 */
export interface PathNode {
  nodeId: string
  /** 排序序号，从 1 开始 */
  order: number
  title: string
  description?: string
  /** 绑定的学习资源 */
  resource?: {
    resourceId: string
    type: ResourceType
    url: string
  }
  /** 完成状态 */
  status: PathNodeStatus
}

/**
 * 学习路径完整响应（GET /sessions/{sessionId}/learning-path）
 */
export interface LearningPathResponse {
  pathId: string
  /** 更新时间（ISO8601） */
  updatedAt: string
  nodes: PathNode[]
}
