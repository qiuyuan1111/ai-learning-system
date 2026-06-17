import { IncomingMessage } from 'http'
import { parse as parseUrl } from 'url'
import { WebSocketServer, WebSocket } from 'ws'
import { verifyToken } from '../utils/jwt'
import connectionManager from '../ws/connection'
import { handleClientMessage } from '../ws/router'

export const wss = new WebSocketServer({ noServer: true })

/**
 * Handle HTTP Upgrade events to connect WebSockets
 */
export function handleUpgrade(req: IncomingMessage, socket: any, head: Buffer): void {
  const parsedUrl = parseUrl(req.url || '', true)
  const pathname = parsedUrl.pathname
  
  if (pathname !== '/ws/chat') {
    socket.destroy()
    return
  }

  const token = parsedUrl.query.token as string
  if (!token) {
    console.warn('[WSUpgrade] Rejecting upgrade request: missing token')
    socket.write('HTTP/1.1 401 Unauthorized\r\n\r\n')
    socket.destroy()
    return
  }

  try {
    const decoded = verifyToken(token)
    const sessionId = decoded.sessionId

    wss.handleUpgrade(req, socket, head, (ws) => {
      // Register new connection
      connectionManager.add(sessionId, ws)

      // Handle message events
      ws.on('message', (message: any) => {
        handleClientMessage(sessionId, message.toString())
      })

      // Handle connection close
      ws.on('close', () => {
        connectionManager.remove(sessionId)
      })

      // Handle socket error
      ws.on('error', (err) => {
        console.error(`[WS] Connection error for session ${sessionId}:`, err)
        connectionManager.remove(sessionId)
      })
    })
  } catch (error) {
    console.warn('[WSUpgrade] Rejecting upgrade request: invalid or expired token')
    socket.write('HTTP/1.1 401 Unauthorized\r\n\r\n')
    socket.destroy()
  }
}
