import { Router, Request, Response } from 'express'
import { createProxyMiddleware } from 'http-proxy-middleware'
import { restRoutes } from '../config/routes'
import { config } from '../config'
import { authMiddleware } from '../middleware/auth'
import {
  getMockTaskStatus,
  getMockLearningPath,
  getMockEvaluationReport,
} from '../mock/responses'
import { generateTraceId } from '../utils/idgen'

export const proxyRouter = Router()

// Apply authentication middleware to all api routes except /api/v1/sessions
proxyRouter.use((req, res, next) => {
  if (req.path === '/api/v1/sessions' && req.method === 'POST') {
    return next()
  }
  return authMiddleware(req, res, next)
})

if (config.mockMode) {
  console.log('[Gateway] REST Proxy is running in MOCK mode.')

  // Mock GET /api/v1/resource-tasks/:taskId
  proxyRouter.get('/api/v1/resource-tasks/:taskId', (req: Request, res: Response) => {
    const { taskId } = req.params as any
    res.json(getMockTaskStatus(taskId))
  })

  // Mock GET /api/v1/sessions/:sessionId/resources
  proxyRouter.get('/api/v1/sessions/:sessionId/resources', (req: Request, res: Response) => {
    const { sessionId } = req.params as any
    // Re-use task status completed resources for mock resources list
    const mockData = getMockTaskStatus('mock_task')
    res.json({
      code: 200,
      message: 'SUCCESS',
      data: {
        list: mockData.data.result?.resources || [],
        pageInfo: {
          page: 1,
          pageSize: 10,
          total: 2,
          totalPages: 1,
        },
      },
      requestId: generateTraceId(),
    })
  })

  // Mock GET /api/v1/sessions/:sessionId/learning-path
  proxyRouter.get('/api/v1/sessions/:sessionId/learning-path', (req: Request, res: Response) => {
    const { sessionId } = req.params as any
    res.json(getMockLearningPath(sessionId))
  })

  // Mock POST /api/v1/sessions/:sessionId/recommend
  proxyRouter.post('/api/v1/sessions/:sessionId/recommend', (req: Request, res: Response) => {
    res.json({
      code: 200,
      message: 'SUCCESS',
      data: { status: 'triggered' },
      requestId: generateTraceId(),
    })
  })

  // Mock POST /api/v1/evaluation/submit
  proxyRouter.post('/api/v1/evaluation/submit', (req: Request, res: Response) => {
    res.json({
      code: 200,
      message: 'SUCCESS',
      data: { status: 'submitted' },
      requestId: generateTraceId(),
    })
  })

  // Mock GET /api/v1/sessions/:sessionId/evaluation-report
  proxyRouter.get('/api/v1/sessions/:sessionId/evaluation-report', (req: Request, res: Response) => {
    const { sessionId } = req.params as any
    res.json(getMockEvaluationReport(sessionId))
  })
} else {
  console.log('[Gateway] REST Proxy is running in PROXY mode.')

  // Configure actual proxies for microservices
  restRoutes.forEach((route) => {
    const proxyOptions: any = {
      target: route.target,
      changeOrigin: route.changeOrigin,
      // 关键：express 用 mount path（proxyRouter.use(route.path, ...)）挂载时，
      // 会把 req.url 改写成"匹配后的剩余路径"（如精确匹配时变成 '/'），
      // 导致 http-proxy-middleware 转发丢掉前缀、后端 404。
      // 这里用 pathRewrite 函数从 req.originalUrl 还原完整请求路径；
      // evaluator 后端不带 /api/v1，再剥掉它；rg/pp 带前缀，原样转发。
      pathRewrite: (_path: string, req: any) => {
        const full = req.originalUrl || req.url
        return route.stripApiV1 ? full.replace(/^\/api\/v1/, '') : full
      },
      logLevel: 'debug',
      onError: (err: any, req: Request, res: Response) => {
        res.status(502).json({
          code: 502,
          message: `Bad Gateway: Target service at ${route.target} is unreachable`,
          data: null,
          requestId: req.traceId || '',
        })
      },
    }

    proxyRouter.use(route.path, createProxyMiddleware(proxyOptions))
  })
}
