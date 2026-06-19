import express from 'express'
import cors from 'cors'
import http from 'http'
import { config } from './config'
import { loggerMiddleware } from './middleware/logger'
import { rateLimiterMiddleware } from './middleware/rateLimiter'
import { errorHandlerMiddleware } from './middleware/errorHandler'
import { getMockSessionCreate } from './mock/responses'
import { proxyRouter } from './routes/proxy'
import { handleUpgrade } from './routes/ws'
import connectionManager from './ws/connection'

const app = express()

// Enable CORS
app.use(cors())

// Logger middleware
app.use(loggerMiddleware)

// Rate limiting middleware
app.use(rateLimiterMiddleware)

// Dedicated parser-enabled route for creating sessions (local routing)
app.post('/api/v1/sessions', express.json(), (req, res) => {
  const { nickname, major, grade } = req.body
  if (!nickname || !major || !grade) {
    res.status(400).json({
      code: 400,
      message: 'Missing required parameters: nickname, major, grade',
      data: null,
      requestId: (req as any).traceId
    })
    return
  }
  
  // Create mock session and token
  const result = getMockSessionCreate(nickname, major, grade)
  res.json(result)
})

// Internal route for backend microservices to push messages to client WebSockets
app.post('/api/v1/internal/sessions/:sessionId/push', express.json(), (req, res) => {
  const { sessionId } = req.params
  const message = req.body

  console.log(`[Gateway] Internal WS push request received for session ${sessionId}: type=${message.type}`)
  connectionManager.send(sessionId, message)

  res.json({
    code: 200,
    message: 'SUCCESS',
    data: null,
    requestId: (req as any).traceId
  })
})

// Proxy routes (proxies handle parsing or direct forwarding)
app.use(proxyRouter)

// Fallback 404 route
app.use((req, res) => {
  res.status(404).json({
    code: 404,
    message: `Resource not found: ${req.method} ${req.path}`,
    data: null,
    requestId: (req as any).traceId
  })
})

// Global error handling
app.use(errorHandlerMiddleware)

// Create HTTP server
const server = http.createServer(app)

// Attach WebSocket Upgrade handler
server.on('upgrade', (req, socket, head) => {
  handleUpgrade(req, socket, head)
})

// Start Server
server.listen(config.port, () => {
  console.log(`[Gateway] Server running at http://localhost:${config.port}`)
  console.log(`[Gateway] Target Profile Service: ${config.services.profile}`)
  console.log(`[Gateway] Target Tutor Service: ${config.services.tutor}`)
})

export { server }

