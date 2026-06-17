/**
 * 学习路径节点状态枚举
 *
 * 单个学习节点（如"RNN与LSTM"一章）的完成进度。
 */
export const PathNodeStatusEnum = {
  /** 待学习 */
  PENDING: 'pending',
  /** 进行中 */
  IN_PROGRESS: 'in_progress',
  /** 已完成 */
  COMPLETED: 'completed',
} as const

/** 路径节点状态：pending | in_progress | completed */
export type PathNodeStatus = typeof PathNodeStatusEnum[keyof typeof PathNodeStatusEnum]
