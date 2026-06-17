import type { ResourceType } from '../enums/ResourceTypeEnum'

/**
 * 资源对象（见 work-person-c.md 3.2.4）
 */
export interface Resource {
  resourceId: string
  type: ResourceType
  title: string
  url: string
  thumbnailUrl?: string
  description?: string
  metadata?: Record<string, unknown>
  /** 创建时间（ISO8601） */
  createdAt: string
}

/**
 * REST API: 获取资源列表请求参数
 * GET /sessions/{sessionId}/resources
 */
export interface GetResourcesParams {
  /** 筛选资源类型，不传则查全部 */
  type?: ResourceType
  page: number
  pageSize: number
}

/**
 * REST API: 获取资源列表响应
 * 外层包 ApiResponse<PaginatedData<Resource>>
 */
export type GetResourcesResponse = Resource[]
