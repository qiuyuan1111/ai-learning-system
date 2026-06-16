import { Request, Response, NextFunction } from 'express'
import { generateTraceId } from '../utils/idgen'

export function loggerMiddleware(req: Request, res: Response, next: NextFunction) {
  req.traceId = (req.headers['x-request-id'] as string) || generateTraceId()
  res.setHeader('X-Request-ID', req.traceId)

  const startTime = Date.now()
  const { method, url } = req

  res.on('finish', () => {
    const duration = Date.now() - startTime
    const { statusCode } = res
    console.log(`[${new Date().toISOString()}] [${req.traceId}] ${method} ${url} ${statusCode} - ${duration}ms`)
  })

  next()
}
