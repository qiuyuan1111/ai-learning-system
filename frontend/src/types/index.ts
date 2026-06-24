// ==========================================
// 1. 通用 API 类型
// ==========================================

export interface ApiResponse<T> {
  code: number
  message: string
  data: T | null
  requestId: string
}

export interface PageInfo {
  page: number
  pageSize: number
  total: number
  totalPages: number
}

export interface PaginatedData<T> {
  list: T[]
  pageInfo: PageInfo
}

// ==========================================
// 2. 会话相关类型
// ==========================================

export interface CreateSessionRequest {
  nickname: string
  major: string
  grade: string
}

export interface CreateSessionResponse {
  sessionId: string
  token: string
  profile: Record<string, any>
}

// ==========================================
// 3. 聊天与消息相关类型
// ==========================================

export interface Attachment {
  type: 'image' | 'file'
  url: string
  mimeType: string
}

export interface DialogueTurn {
  role: 'user' | 'assistant'
  content: string
}

export interface ClientMessage {
  msgId: string
  intent: 'profile_build' | 'profile_update' | 'resource_generate' | 'tutoring' | 'path_query' | 'evaluate'
  content: {
    text: string
    attachments?: Attachment[]
  }
  context?: {
    resourceId?: string
    courseId?: string
    // 联动数据通道：tutor 答疑后动态更新画像时，携带最近几轮问答原文给 profile 服务
    dialogue?: DialogueTurn[]
  }
}

export interface TextContent {
  markdown: string
}

export interface ResourceCard {
  resourceId: string
  resourceType: 'mindmap' | 'ppt' | 'pdf' | 'doc' | 'video'
  title: string
  url: string
  description?: string
  thumbnailUrl?: string
}

export interface ProgressContent {
  taskId: string
  progress: number // 0-100
  description: string
}

export interface ErrorContent {
  code: number
  message: string
}

export interface ServerMessage {
  msgId: string
  replyTo: string
  intent: string
  type: 'text' | 'resource_card' | 'progress' | 'done' | 'error'
  content: TextContent | ResourceCard | ProgressContent | ErrorContent
}

// ==========================================
// 4. 学习资源相关类型
// ==========================================

export interface Resource {
  resourceId: string
  type: 'ppt' | 'pdf' | 'doc' | 'mindmap' | 'video'
  title: string
  url: string
  thumbnailUrl?: string
  metadata?: Record<string, any>
  createdAt: string
}

export type TaskStatus = 'pending' | 'processing' | 'completed' | 'failed'

export interface TaskResponse {
  taskId: string
  status: TaskStatus
  progress: number
  result?: {
    resources: Resource[]
  }
}

// ==========================================
// 5. 学习路径相关类型
// ==========================================

export interface PathNode {
  nodeId: string
  order: number
  title: string
  resource?: {
    resourceId: string
    type: string
    url: string
  }
  status: 'pending' | 'in_progress' | 'completed'
}

export interface LearningPathResponse {
  pathId: string
  updatedAt: string
  nodes: PathNode[]
}

// ==========================================
// 6. 学习评估相关类型
// ==========================================

export interface Answer {
  questionId: string
  answer: string
  timeSpent: number // 单位：秒
}

export interface Behavior {
  action: string
  resourceId: string
  timestamp: string
}

export interface SubmitEvaluationRequest {
  sessionId: string
  quizId: string
  answers: Answer[]
  behaviors: Behavior[]
}

export interface EvaluationDimension {
  name: string
  score: number
  maxScore: number
}

export interface EvaluationReport {
  dimensions: EvaluationDimension[]
  weakPoints: string[]
  suggestions: string[]
}
