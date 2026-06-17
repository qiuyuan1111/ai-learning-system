/**
 * 意图枚举
 *
 * 用于 WebSocket 聊天帧的 intent 字段，区分用户消息的业务类型。
 * 详见 api.md 2.2 节。
 */
export const IntentEnum = {
  /** 对话式画像构建 */
  PROFILE_BUILD: 'profile_build',
  /** 资源生成 */
  RESOURCE_GENERATE: 'resource_generate',
  /** 智能辅导 / 答疑 */
  TUTORING: 'tutoring',
  /** 学习路径查询 */
  PATH_QUERY: 'path_query',
  /** 学习效果评估 */
  EVALUATE: 'evaluate',
} as const

/** 意图类型：profile_build | resource_generate | tutoring | path_query | evaluate */
export type Intent = typeof IntentEnum[keyof typeof IntentEnum]
