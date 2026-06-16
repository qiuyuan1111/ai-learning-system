import type { ServerMessage, ClientMessage } from '../types'

type MessageCallback = (msg: ServerMessage) => void

export class WebSocketClient {
  private ws: WebSocket | null = null
  private url: string = ''
  private token: string = ''
  private callbacks: Set<MessageCallback> = new Set()
  private stateCallbacks: Set<(status: 'CONNECTING' | 'OPEN' | 'CLOSING' | 'CLOSED') => void> = new Set()
  
  private reconnectAttempts: number = 0
  private maxReconnectDelay: number = 30000
  private reconnectTimer: any = null
  private isIntentionalClose: boolean = false

  constructor() {
    const wsHost = (import.meta.env.VITE_WS_BASE_URL as string) || 'ws://localhost:3000/ws/chat'
    this.url = wsHost
  }

  public connect(token: string): void {
    if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
      return
    }
    
    this.token = token
    this.isIntentionalClose = false
    this.notifyState('CONNECTING')

    try {
      this.ws = new WebSocket(`${this.url}?token=${encodeURIComponent(token)}`)

      this.ws.onopen = () => {
        console.log('[WebSocket] Connection opened')
        this.reconnectAttempts = 0
        this.notifyState('OPEN')
      }

      this.ws.onmessage = (event) => {
        try {
          const message: ServerMessage = JSON.parse(event.data)
          this.callbacks.forEach((cb) => cb(message))
        } catch (e) {
          console.error('[WebSocket] Failed to parse message', e)
        }
      }

      this.ws.onclose = (event) => {
        console.log('[WebSocket] Connection closed', event)
        this.notifyState('CLOSED')
        this.ws = null

        if (!this.isIntentionalClose) {
          this.reconnect()
        }
      }

      this.ws.onerror = (error) => {
        console.error('[WebSocket] Error occurred', error)
        this.notifyState('CLOSED')
      }
    } catch (e) {
      console.error('[WebSocket] Failed to establish connection', e)
      this.notifyState('CLOSED')
      this.reconnect()
    }
  }

  public send(intent: ClientMessage['intent'], text: string, context?: ClientMessage['context']): string {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      console.error('[WebSocket] Cannot send message, socket is not open')
      return ''
    }

    const msgId = 'msg_' + Math.random().toString(36).substr(2, 9)
    const clientMsg: ClientMessage = {
      msgId,
      intent,
      content: {
        text,
      },
      context,
    }

    this.ws.send(JSON.stringify(clientMsg))
    return msgId
  }

  public onMessage(callback: MessageCallback): () => void {
    this.callbacks.add(callback)
    return () => {
      this.callbacks.delete(callback)
    }
  }

  public onStatusChange(callback: (status: 'CONNECTING' | 'OPEN' | 'CLOSING' | 'CLOSED') => void): () => void {
    this.stateCallbacks.add(callback)
    // Send current status immediately
    callback(this.getStatus())
    return () => {
      this.stateCallbacks.delete(callback)
    }
  }

  public disconnect(): void {
    this.isIntentionalClose = true
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }

  public getStatus(): 'CONNECTING' | 'OPEN' | 'CLOSING' | 'CLOSED' {
    if (!this.ws) return 'CLOSED'
    switch (this.ws.readyState) {
      case WebSocket.CONNECTING:
        return 'CONNECTING'
      case WebSocket.OPEN:
        return 'OPEN'
      case WebSocket.CLOSING:
        return 'CLOSING'
      case WebSocket.CLOSED:
      default:
        return 'CLOSED'
    }
  }

  private reconnect(): void {
    if (this.reconnectTimer || this.isIntentionalClose) return

    this.reconnectAttempts++
    // Exponential backoff: 1s, 2s, 4s, 8s, up to 30s
    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts - 1), this.maxReconnectDelay)
    console.log(`[WebSocket] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`)

    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null
      this.connect(this.token)
    }, delay)
  }

  private notifyState(status: 'CONNECTING' | 'OPEN' | 'CLOSING' | 'CLOSED'): void {
    this.stateCallbacks.forEach((cb) => cb(status))
  }
}

// Export a single instance to be shared across components
export const wsClient = new WebSocketClient()
export default wsClient
