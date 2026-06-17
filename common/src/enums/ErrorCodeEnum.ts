/**
 * 业务错误码枚举
 *
 * 统一响应体 ApiResponse.code 的取值，0 表示成功，其余为各类异常。
 * 与 api.md 3.2 节错误码表保持一致，全系统共享。
 *
 * 编码段约定：
 *   1xxx — 请求/会话层错误
 *   2xxx — 资源生成层错误
 *   3xxx — 内容安全 / 防幻觉
 *   4xxx — 智能体超时
 *   5xxx — 系统未知错误
 */
export const ErrorCodeEnum = {
  /** 成功 */
  SUCCESS: 0,
  /** 参数缺失或格式错误 */
  PARAM_ERROR: 1001,
  /** 会话不存在 */
  SESSION_NOT_FOUND: 1002,
  /** 资源生成任务不存在 */
  TASK_NOT_FOUND: 2001,
  /** 资源生成失败（含原因） */
  RESOURCE_GEN_FAILED: 2002,
  /** 内容安全审核未通过 */
  CONTENT_SAFETY_VIOLATION: 3001,
  /** 防幻觉校验未通过，未生成回答 */
  HALLUCINATION_DETECTED: 3002,
  /** 智能体服务超时 */
  AGENT_TIMEOUT: 4001,
  /** 系统未知错误 */
  UNKNOWN_ERROR: 5000,
} as const

/** 业务错误码类型 */
export type ErrorCode = typeof ErrorCodeEnum[keyof typeof ErrorCodeEnum]
