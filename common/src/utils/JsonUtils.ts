/**
 * JSON 工具函数
 *
 * 包装原生 JSON 操作，提供更安全的解析/序列化能力，
 * 避免脏数据或循环引用导致服务进程崩溃。
 *
 * 说明：此为内部辅助工具，不参与对外请求/响应契约。
 */
export class JsonUtils {
  /**
   * 安全解析 JSON 字符串。
   * 解析失败（格式错误或入参为空）时返回 fallback，绝不抛异常。
   *
   * @param text     待解析的字符串
   * @param fallback 解析失败时的返回值，默认 null
   */
  static safeParse<T = unknown>(text: string | null | undefined, fallback: T | null = null): T | null {
    if (text == null || text === '') return fallback
    try {
      return JSON.parse(text) as T
    } catch {
      return fallback
    }
  }

  /**
   * 安全序列化为 JSON 字符串。
   * 遇到循环引用等无法序列化的情况时，返回兜底字符串而非抛错。
   */
  static safeStringify(value: unknown): string {
    try {
      return JSON.stringify(value)
    } catch {
      return JSON.stringify({ error: 'unable_to_serialize' })
    }
  }

  /**
   * 美化输出（2 空格缩进），便于日志和调试打印。
   */
  static pretty(value: unknown): string {
    try {
      return JSON.stringify(value, null, 2)
    } catch {
      return String(value)
    }
  }

  /**
   * 基于 JSON 的深拷贝。
   * 注意：无法拷贝函数、undefined、Date、Map/Set 等特殊对象，
   * 仅适用于纯数据 DTO。
   */
  static clone<T>(value: T): T {
    return JSON.parse(JSON.stringify(value)) as T
  }
}
