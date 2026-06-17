/**
 * 用户画像 — 6 个维度（见 work-person-c.md 3.2.3 / api.md 5.4）
 *
 * 所有智能体共享此画像定义。
 * 画像在对话过程中逐步构建，初始可能部分维度为 null（即对应字段缺失）。
 */
export interface UserProfile {
  /** 会话 ID */
  sessionId: string
  /** 各维度信息 */
  dimensions: ProfileDimensions
  /** 最近更新时间（ISO8601） */
  updatedAt: string
  /** 版本号，每次更新递增 */
  version: number
}

export interface ProfileDimensions {
  /** 知识基础 */
  knowledgeBase?: {
    /** 水平: beginner | intermediate | advanced */
    level: string
    /** 已掌握的知识标签，如 ["机器学习", "Python"] */
    tags: string[]
    /** 置信度 0-1 */
    confidence: number
  }
  /** 认知风格: theoretical | practical | visual | verbal */
  cognitiveStyle?: {
    style: string
    detail?: string
    confidence: number
  }
  /** 学习节奏: slow | moderate | fast */
  learningPace?: {
    pace: string
    /** 单次专注时长（分钟） */
    preferredSessionMinutes?: number
    confidence: number
  }
  /** 易错点列表 */
  weaknessPreferences?: Array<{
    /** 薄弱知识点标签 */
    weakTags: string[]
    description?: string
    confidence: number
  }>
  /** 兴趣领域列表 */
  interestAreas?: Array<{
    areas: string[]
    /** 兴趣深度 1-5 */
    depth: number
    confidence: number
  }>
  /** 目标难度 1-10 */
  targetDifficulty?: {
    level: number
    description?: string
    confidence: number
  }
}
