/**
 * 评估提交请求（POST /evaluation/submit，见 work-person-c.md 3.2.7 / api.md 2.5.1）
 */
export interface SubmitEvaluationRequest {
  sessionId: string
  quizId: string
  answers: AnswerItem[]
  behaviors: BehaviorItem[]
}

export interface AnswerItem {
  questionId: string
  answer: string
  /** 作答耗时（秒） */
  timeSpent: number
}

export interface BehaviorItem {
  /** 行为类型: video_pause | video_forward | video_rewind | resource_view */
  action: string
  resourceId: string
  timestamp: string
}

/**
 * 评估报告（GET /sessions/{sessionId}/evaluation-report）
 */
export interface EvaluationReport {
  dimensions: EvaluationDimension[]
  weakPoints: WeakPoint[]
  suggestions: string[]
}

export interface EvaluationDimension {
  name: string
  score: number
  maxScore: number
}

export interface WeakPoint {
  topic: string
  /** 严重程度 1-5 */
  severity: number
  description: string
  suggestion?: string
}
