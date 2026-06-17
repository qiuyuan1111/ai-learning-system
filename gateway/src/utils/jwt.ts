import jwt from 'jsonwebtoken'
import { config } from '../config'

export interface SessionPayload {
  sessionId: string
  nickname: string
  major: string
  grade: string
}

/**
 * Sign a session payload to generate a JWT token
 */
export function signToken(payload: SessionPayload): string {
  return jwt.sign(payload, config.jwtSecret, { expiresIn: '7d' })
}

/**
 * Verify a JWT token and return the decoded payload
 */
export function verifyToken(token: string): SessionPayload {
  return jwt.verify(token, config.jwtSecret) as SessionPayload
}
