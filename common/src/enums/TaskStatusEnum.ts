/**
 * 异步任务状态枚举
 *
 * 资源生成等耗时任务的生命周期状态。
 */
export const TaskStatusEnum = {
  /** 待处理（已创建，尚未开始） */
  PENDING: 'pending',
  /** 处理中 */
  PROCESSING: 'processing',
  /** 已完成 */
  COMPLETED: 'completed',
  /** 已失败 */
  FAILED: 'failed',
} as const

/** 任务状态：pending | processing | completed | failed */
export type TaskStatus = typeof TaskStatusEnum[keyof typeof TaskStatusEnum]
