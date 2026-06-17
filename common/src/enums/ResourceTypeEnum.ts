/**
 * 资源类型枚举
 *
 * 资源生成器可产出的多模态资源种类，对应赛题要求的"至少 5 种类型"。
 */
export const ResourceTypeEnum = {
  PPT: 'ppt',
  PDF: 'pdf',
  DOC: 'doc',
  MINDMAP: 'mindmap',
  VIDEO: 'video',
} as const

/** 资源类型：ppt | pdf | doc | mindmap | video */
export type ResourceType = typeof ResourceTypeEnum[keyof typeof ResourceTypeEnum]
