import { randomUUID } from 'crypto'

/**
 * Generate a unique trace ID (UUID v4)
 */
export function generateTraceId(): string {
  return randomUUID()
}
