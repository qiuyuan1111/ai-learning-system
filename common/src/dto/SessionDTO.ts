/**
 * 创建会话请求（POST /sessions 请求体，见 api.md 2.1.1）
 *
 * 仅需极少量信息，其余画像通过对话补全。
 */
export interface CreateSessionRequest {
  /** 用户昵称 */
  nickname: string
  /** 专业 */
  major: string
  /** 年级，如 "本科三年级" */
  grade: string
}

/**
 * 创建会话响应（POST /sessions 响应 data）
 */
export interface CreateSessionResponse {
  /** 会话 ID，格式 sess_xxx */
  sessionId: string
  /** JWT Token */
  token: string
  /** 初始画像（维度可能不全） */
  profile: Record<string, unknown>
}
