import { randomBytes, randomUUID } from 'crypto'

/**
 * ID 生成器
 *
 * 生成全系统统一的、带可读前缀的唯一 ID，便于从 ID 直观判断对象类型。
 *
 * 格式约定（见 work-person-c.md 3.4）：
 *   会话 ID  → sess_  + 16 位随机串
 *   资源 ID  → res_   + 16 位随机串
 *   任务 ID  → task_  + 16 位随机串
 *   路径 ID  → path_  + 16 位随机串
 *   请求 ID  → UUID v4（用于链路追踪）
 *
 * 实现使用 Node 内置 crypto 模块，无需额外依赖。
 */
export class IdGenerator {
  /**
   * 生成指定位数的随机十六进制字符串
   * 每 2 位 hex 对应 1 字节，故按需向上取整后再截断到目标长度。
   */
  private static randomHex(length = 16): string {
    return randomBytes(Math.ceil(length / 2)).toString('hex').slice(0, length)
  }

  /** 拼接「前缀_随机串」 */
  private static prefixed(prefix: string): string {
    return `${prefix}_${this.randomHex(16)}`
  }

  /** 生成会话 ID，格式 sess_xxxxxxxxxxxxxxxx */
  static sessionId(): string {
    return this.prefixed('sess')
  }

  /** 生成资源 ID，格式 res_xxxxxxxxxxxxxxxx */
  static resourceId(): string {
    return this.prefixed('res')
  }

  /** 生成任务 ID，格式 task_xxxxxxxxxxxxxxxx */
  static taskId(): string {
    return this.prefixed('task')
  }

  /** 生成路径 ID，格式 path_xxxxxxxxxxxxxxxx */
  static pathId(): string {
    return this.prefixed('path')
  }

  /** 生成请求追踪 ID（UUID v4） */
  static requestId(): string {
    return randomUUID()
  }
}
