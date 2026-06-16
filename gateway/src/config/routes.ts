import { config } from './index'

export interface RouteMapping {
  path: string
  target: string
  changeOrigin: boolean
  pathRewrite?: Record<string, string>
}

export const restRoutes: RouteMapping[] = [
  {
    path: '/api/v1/resource-tasks',
    target: config.services.resourceGen,
    changeOrigin: true,
    pathRewrite: { '^/api/v1/resource-tasks': '/resource-tasks' }
  },
  {
    path: '/api/v1/sessions/:sessionId/resources',
    target: config.services.resourceGen,
    changeOrigin: true,
    pathRewrite: (pathStr: string, req: any) => {
      // Re-map /api/v1/sessions/:sessionId/resources to /sessions/:sessionId/resources
      return pathStr.replace('/api/v1', '')
    }
  } as any,
  {
    path: '/api/v1/sessions/:sessionId/learning-path',
    target: config.services.pathPlanner,
    changeOrigin: true,
    pathRewrite: (pathStr: string, req: any) => {
      return pathStr.replace('/api/v1', '')
    }
  } as any,
  {
    path: '/api/v1/sessions/:sessionId/recommend',
    target: config.services.pathPlanner,
    changeOrigin: true,
    pathRewrite: (pathStr: string, req: any) => {
      return pathStr.replace('/api/v1', '')
    }
  } as any,
  {
    path: '/api/v1/evaluation',
    target: config.services.evaluator,
    changeOrigin: true,
    pathRewrite: { '^/api/v1/evaluation': '/evaluation' }
  },
  {
    path: '/api/v1/sessions/:sessionId/evaluation-report',
    target: config.services.evaluator,
    changeOrigin: true,
    pathRewrite: (pathStr: string, req: any) => {
      return pathStr.replace('/api/v1', '')
    }
  } as any
]
