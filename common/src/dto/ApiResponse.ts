import { IdGenerator } from '../utils/IdGenerator'
import { ErrorCodeEnum } from '../enums/ErrorCodeEnum'

/**
 * 通用 API 响应体
 *
 * 所有非流式 REST 接口统一使用此结构返回（见 api.md 1.5 节）。
 *
 * @template T - data 字段的具体数据类型
 *
 * 示例:
 *   { code: 0, message: "success", data: { sessionId: "..." }, requestId: "uuid" }
 *   { code: 3001, message: "内容违规已拦截", data: null, requestId: "uuid" }
 */
export interface ApiResponse<T = unknown> {
  /** 业务状态码，0 表示成功，非 0 表示异常 */
  code: number
  /** 提示信息 */
  message: string
  /** 具体返回数据，可为对象、数组或 null */
  data: T | null
  /** 请求追踪 ID，用于链路追踪和日志排查 */
  requestId: string
}

/**
 * 快捷构造成功响应
 *
 * @param data       返回数据
 * @param requestId  可选，未传时自动生成 UUID
 */
export function success<T>(data: T, requestId?: string): ApiResponse<T> {
  return {
    code: ErrorCodeEnum.SUCCESS,
    message: 'success',
    data,
    requestId: requestId ?? IdGenerator.requestId(),
  }
}

/**
 * 快捷构造错误响应
 *
 * @param code       错误码（见 ErrorCodeEnum）
 * @param message    错误提示信息
 * @param requestId  可选，未传时自动生成 UUID
 */
export function error(code: number, message: string, requestId?: string): ApiResponse<null> {
  return {
    code,
    message,
    data: null,
    requestId: requestId ?? IdGenerator.requestId(),
  }
}
