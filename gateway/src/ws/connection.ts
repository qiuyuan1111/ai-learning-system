import { WebSocket } from 'ws'

export class ConnectionManager {
  // Map sessionId to client WebSocket connection
  private connections = new Map<string, WebSocket>()

  public add(sessionId: string, ws: WebSocket): void {
    this.connections.set(sessionId, ws)
    console.log(`[ConnectionManager] Added connection for session: ${sessionId}. Total: ${this.connections.size}`)
  }

  public remove(sessionId: string): void {
    if (this.connections.has(sessionId)) {
      this.connections.delete(sessionId)
      console.log(`[ConnectionManager] Removed connection for session: ${sessionId}. Total: ${this.connections.size}`)
    }
  }

  public get(sessionId: string): WebSocket | undefined {
    return this.connections.get(sessionId)
  }

  public send(sessionId: string, message: any): void {
    const ws = this.connections.get(sessionId)
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(message))
    } else {
      console.warn(`[ConnectionManager] Cannot send message, session ${sessionId} is not connected or open`)
    }
  }
}

export const connectionManager = new ConnectionManager()
export default connectionManager
