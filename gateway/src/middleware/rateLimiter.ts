import { Request, Response, NextFunction } from 'express'

// Simple in-memory storage for tracking client requests by IP
const requestLogs: Map<string, number[]> = new Map()

// Configuration: Allow maximum 100 requests per 1 minute (60,000 milliseconds) window
const WINDOW_MS = 60 * 1000 // 1 minute
const MAX_REQUESTS = 100

export function rateLimiterMiddleware(req: Request, res: Response, next: NextFunction): void {
  const ip = req.ip || req.socket.remoteAddress || 'unknown'
  const now = Date.now()

  if (!requestLogs.has(ip)) {
    requestLogs.set(ip, [])
  }

  const timestamps = requestLogs.get(ip)!

  // Filter out request timestamps that are older than the sliding window
  const activeTimestamps = timestamps.filter((timestamp) => now - timestamp < WINDOW_MS)

  if (activeTimestamps.length >= MAX_REQUESTS) {
    console.warn(`[RateLimiter] IP ${ip} exceeded rate limit of ${MAX_REQUESTS} requests/min`)
    res.status(429).json({
      code: 429,
      message: '请求过于频繁，请稍后再试',
      data: null,
      requestId: req.traceId || '',
    })
    return
  }

  // Record current request timestamp
  activeTimestamps.push(now)
  requestLogs.set(ip, activeTimestamps)

  next()
}
