import { Request, Response, NextFunction } from 'express'

export function errorHandlerMiddleware(err: any, req: Request, res: Response, next: NextFunction) {
  const statusCode = err.status || err.statusCode || 500
  const message = err.message || 'Internal Server Error'
  const requestId = req.traceId || ''

  console.error(`[Error] [${requestId}] ${statusCode} - ${message}`, err)

  res.status(statusCode).json({
    code: statusCode,
    message: message,
    data: null,
    requestId: requestId
  })
}
