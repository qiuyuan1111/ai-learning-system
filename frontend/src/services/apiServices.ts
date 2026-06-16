import api from './api'
import type {
  CreateSessionRequest,
  CreateSessionResponse,
  ApiResponse,
  TaskResponse,
  PaginatedData,
  Resource,
  LearningPathResponse,
  SubmitEvaluationRequest,
  EvaluationReport
} from '../types'

/**
 * 创建会话 API
 */
export async function createSession(data: CreateSessionRequest): Promise<CreateSessionResponse> {
  const response: ApiResponse<CreateSessionResponse> = await api.post('/sessions', data)
  if (response.code !== 200 || !response.data) {
    throw new Error(response.message || 'Failed to create session')
  }
  return response.data
}

/**
 * 轮询异步任务进度 API
 */
export async function getTaskStatus(taskId: string): Promise<TaskResponse> {
  const response: ApiResponse<TaskResponse> = await api.get(`/resource-tasks/${taskId}`)
  if (response.code !== 200 || !response.data) {
    throw new Error(response.message || 'Failed to get task status')
  }
  return response.data
}

/**
 * 获取会话生成的资源列表 API
 */
export async function getResources(
  sessionId: string,
  params?: { type?: string; page: number; pageSize: number }
): Promise<PaginatedData<Resource>> {
  const response: ApiResponse<PaginatedData<Resource>> = await api.get(
    `/sessions/${sessionId}/resources`,
    { params }
  )
  if (response.code !== 200 || !response.data) {
    throw new Error(response.message || 'Failed to get resources')
  }
  return response.data
}

/**
 * 获取学习路径树 API
 */
export async function getLearningPath(sessionId: string): Promise<LearningPathResponse> {
  const response: ApiResponse<LearningPathResponse> = await api.get(
    `/sessions/${sessionId}/learning-path`
  )
  if (response.code !== 200 || !response.data) {
    throw new Error(response.message || 'Failed to get learning path')
  }
  return response.data
}

/**
 * 触发路径更新/推荐算法 API
 */
export async function triggerRecommend(sessionId: string): Promise<any> {
  const response: ApiResponse<any> = await api.post(`/sessions/${sessionId}/recommend`)
  if (response.code !== 200) {
    throw new Error(response.message || 'Failed to trigger recommendation')
  }
  return response.data
}

/**
 * 提交评估答卷 API
 */
export async function submitEvaluation(data: SubmitEvaluationRequest): Promise<any> {
  const response: ApiResponse<any> = await api.post('/evaluation/submit', data)
  if (response.code !== 200) {
    throw new Error(response.message || 'Failed to submit evaluation')
  }
  return response.data
}

/**
 * 获取评估报告 API
 */
export async function getEvaluationReport(sessionId: string): Promise<EvaluationReport> {
  const response: ApiResponse<EvaluationReport> = await api.get(
    `/sessions/${sessionId}/evaluation-report`
  )
  if (response.code !== 200 || !response.data) {
    throw new Error(response.message || 'Failed to get evaluation report')
  }
  return response.data
}
