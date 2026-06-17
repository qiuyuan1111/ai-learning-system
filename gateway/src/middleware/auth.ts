import { Request, Response, NextFunction } from 'express'
import { verifyToken } from '../utils/jwt'

export function authMiddleware(req: Request, res: Response, next: NextFunction) {
  const authHeader = req.headers.authorization
  const requestId = req.traceId || ''

  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    res.status(401).json({
      code: 401,
      message: '未认证，请提供有效的 Token',
      data: null,
      requestId: requestId
    })
    return
  }

  const token = authHeader.split(' ')[1]

  try {
    const decoded = verifyToken(token)
    req.session = decoded
    next()
  } catch (error: any) {
    res.status(401).json({
      code: 401,
      message: 'Token 无效或已过期',
      data: null,
      requestId: requestId
    })
  }
}
