import { config } from './index'

export interface RouteMapping {
  path: string
  target: string
  changeOrigin: boolean
  // evaluator 后端路由【不带】/api/v1 前缀，网关需剥掉 /api/v1；
  // resource-gen/path-planner 后端路由【带】/api/v1，网关原样转发。
  // pathRewrite 在 proxy.ts 里用 req.originalUrl 统一处理（见下方说明）。
  stripApiV1?: boolean
}

export const restRoutes: RouteMapping[] = [
  // ── resource-gen / path-planner：后端路由带 /api/v1，原样转发 ──
  { path: '/api/v1/resource-tasks', target: config.services.resourceGen, changeOrigin: true },
  { path: '/api/v1/sessions/:sessionId/resources', target: config.services.resourceGen, changeOrigin: true },
  { path: '/api/v1/sessions/:sessionId/learning-path', target: config.services.pathPlanner, changeOrigin: true },
  { path: '/api/v1/sessions/:sessionId/recommend', target: config.services.pathPlanner, changeOrigin: true },

  // ── evaluator：后端路由不带 /api/v1，网关剥掉 /api/v1 ──
  { path: '/api/v1/evaluation', target: config.services.evaluator, changeOrigin: true, stripApiV1: true },
  { path: '/api/v1/sessions/:sessionId/evaluation-report', target: config.services.evaluator, changeOrigin: true, stripApiV1: true },
]
