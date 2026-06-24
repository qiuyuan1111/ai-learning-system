import { create } from 'zustand'
import type { ServerMessage, TaskResponse } from '../types'

// 用户手动发送的消息气泡（与 ServerMessage 区分开，不参与流式合并）。
// content 直接存字符串，与 MessageBubble 现有契约一致（其读 (message as any).content 字符串）。
export interface UserMessage {
  msgId: string
  sender: 'user'
  content: string
  // 以下字段让 UserMessage 能与 ServerMessage 一起渲染
  intent?: string
  type?: string
  replyTo?: string
}

type ChatMessage = ServerMessage | UserMessage

// 对话型 intent：每个 agent 拥有独立的消息分区（侧边栏切换时不丢上下文）
const CHAT_INTENTS = ['profile_build', 'tutoring', 'resource_generate', 'path_query', 'evaluate'] as const

interface AppState {
  // ==========================================
  // 1. 会话状态 (Session State)
  // ==========================================
  sessionId: string | null
  token: string | null
  profile: any | null

  // ==========================================
  // 2. 聊天与任务状态 (Chat & Task State)
  // ==========================================
  // 当前 intent 分区的消息（派生自 messagesByIntent[currentIntent]，保留以降低消费点回归）
  messages: ChatMessage[]
  // 按 intent 分区的消息存储（独立对话窗口的核心）
  messagesByIntent: Record<string, ChatMessage[]>
  // 各 intent 未读计数（切走后有新消息时，侧边栏显示红点）
  unreadByIntent: Record<string, number>
  isConnected: boolean
  isProcessing: boolean
  activeTasks: Record<string, TaskResponse>
  currentIntent: 'profile_build' | 'tutoring' | 'path_query' | 'evaluate' | 'resource_generate'

  // ==========================================
  // 3. 全局主题状态 (Theme State)
  // ==========================================
  theme: 'light' | 'dark'

  // ==========================================
  // 4. 操作方法 (Actions)
  // ==========================================
  setSession: (sessionId: string, token: string, profile: any) => void
  clearSession: () => void
  addMessage: (message: ServerMessage) => void
  addUserMessage: (intent: string, text: string) => void
  setMessages: (messages: ChatMessage[]) => void
  markIntentRead: (intent: string) => void
  clearIntentMessages: (intent: string) => void
  getMessagesByIntent: (intent: string) => ChatMessage[]
  setConnected: (status: boolean) => void
  setProcessing: (status: boolean) => void
  setCurrentIntent: (intent: AppState['currentIntent']) => void
  updateTask: (taskId: string, task: TaskResponse) => void
  removeTask: (taskId: string) => void
  toggleTheme: () => void
}

// 初始化各分区为空数组
function initialBuckets(): Record<string, ChatMessage[]> {
  const buckets: Record<string, ChatMessage[]> = {}
  for (const i of CHAT_INTENTS) buckets[i] = []
  return buckets
}

export const useAppState = create<AppState>((set, get) => ({
  // 初始值从 localStorage 恢复
  sessionId: localStorage.getItem('sessionId'),
  token: localStorage.getItem('token'),
  profile: localStorage.getItem('profile') ? JSON.parse(localStorage.getItem('profile')!) : null,
  theme: (localStorage.getItem('theme') as 'light' | 'dark') || 'dark',

  messagesByIntent: initialBuckets(),
  unreadByIntent: {},
  messages: [],
  isConnected: false,
  isProcessing: false,
  activeTasks: {},
  currentIntent: 'profile_build',

  setSession: (sessionId, token, profile) => {
    localStorage.setItem('sessionId', sessionId)
    localStorage.setItem('token', token)
    localStorage.setItem('profile', JSON.stringify(profile))
    set({ sessionId, token, profile })
  },

  clearSession: () => {
    localStorage.removeItem('sessionId')
    localStorage.removeItem('token')
    localStorage.removeItem('profile')
    set({
      sessionId: null,
      token: null,
      profile: null,
      messages: [],
      messagesByIntent: initialBuckets(),
      unreadByIntent: {},
      activeTasks: {},
    })
  },

  // 把一条消息写入它所属 intent 的分区，并在分区内做流式文本合并。
  addMessage: (message) => {
    set((state) => {
      const intent = message.intent || state.currentIntent
      const bucket = state.messagesByIntent[intent] ? [...state.messagesByIntent[intent]] : []

      // 避免重复 msgId
      const exists = bucket.some((m) => m.msgId === message.msgId)
      if (exists) {
        const updated = bucket.map((m) => (m.msgId === message.msgId ? (message as ChatMessage) : m))
        const nextByIntent = { ...state.messagesByIntent, [intent]: updated }
        return {
          messagesByIntent: nextByIntent,
          messages: intent === state.currentIntent ? updated : state.messages,
          unreadByIntent: bumpUnread(state.unreadByIntent, intent, state.currentIntent),
        }
      }

      // 流式文本合并：同 intent 分区内，若上一条是助理同类 text，则追加而非新建气泡
      let currentBucket = bucket
      if (message.type === 'text') {
        currentBucket = currentBucket.filter(
          (m) => !(m.type === 'progress' && m.replyTo === message.replyTo)
        )
      }

      if (message.type === 'text' && currentBucket.length > 0) {
        const lastMsg = currentBucket[currentBucket.length - 1]
        const isLastMsgAssistantText =
          !('sender' in lastMsg) &&
          lastMsg.type === 'text' &&
          lastMsg.intent === message.intent

        if (isLastMsgAssistantText) {
          const updatedLastMsg = {
            ...lastMsg,
            content: {
              ...lastMsg.content,
              markdown: ((lastMsg.content as any).markdown || '') + ((message.content as any).markdown || ''),
            },
          } as ChatMessage
          const updated = [...currentBucket.slice(0, -1), updatedLastMsg]
          const nextByIntent = { ...state.messagesByIntent, [intent]: updated }
          return {
            messagesByIntent: nextByIntent,
            messages: intent === state.currentIntent ? updated : state.messages,
            unreadByIntent: bumpUnread(state.unreadByIntent, intent, state.currentIntent),
          }
        }
      }

      const updated = [...currentBucket, message as ChatMessage]
      const nextByIntent = { ...state.messagesByIntent, [intent]: updated }
      return {
        messagesByIntent: nextByIntent,
        messages: intent === state.currentIntent ? updated : state.messages,
        unreadByIntent: bumpUnread(state.unreadByIntent, intent, state.currentIntent),
      }
    })
  },

  // 用户手动发送的消息气泡：写入对应 intent 分区
  addUserMessage: (intent, text) => {
    const userMsg: UserMessage = {
      msgId: 'user_' + Math.random().toString(36).slice(2, 11),
      sender: 'user',
      content: text,
      intent,
      type: 'text',
    }
    set((state) => {
      const bucket = state.messagesByIntent[intent] ? [...state.messagesByIntent[intent]] : []
      const updated = [...bucket, userMsg]
      return {
        messagesByIntent: { ...state.messagesByIntent, [intent]: updated },
        messages: intent === state.currentIntent ? updated : state.messages,
      }
    })
  },

  setMessages: (messages) => {
    set((state) => ({
      messages,
      messagesByIntent: { ...state.messagesByIntent, [state.currentIntent]: messages },
    }))
  },

  markIntentRead: (intent) =>
    set((state) => ({
      unreadByIntent: { ...state.unreadByIntent, [intent]: 0 },
    })),

  clearIntentMessages: (intent) =>
    set((state) => ({
      messagesByIntent: { ...state.messagesByIntent, [intent]: [] },
      messages: intent === state.currentIntent ? [] : state.messages,
    })),

  getMessagesByIntent: (intent) => get().messagesByIntent[intent] || [],

  setConnected: (status) => set({ isConnected: status }),

  setProcessing: (status) => set({ isProcessing: status }),

  // 切换 intent 时，messages 跟随到新分区，并清除该分区未读
  setCurrentIntent: (intent) =>
    set((state) => ({
      currentIntent: intent,
      messages: state.messagesByIntent[intent] || [],
      unreadByIntent: { ...state.unreadByIntent, [intent]: 0 },
    })),

  updateTask: (taskId, task) =>
    set((state) => ({
      activeTasks: {
        ...state.activeTasks,
        [taskId]: task,
      },
    })),

  removeTask: (taskId) =>
    set((state) => {
      const newTasks = { ...state.activeTasks }
      delete newTasks[taskId]
      return { activeTasks: newTasks }
    }),

  toggleTheme: () =>
    set((state) => {
      const nextTheme = state.theme === 'dark' ? 'light' : 'dark'
      localStorage.setItem('theme', nextTheme)
      return { theme: nextTheme }
    }),
}))

// 非 currentIntent 收到消息时，对应分区未读 +1（侧边栏红点）
function bumpUnread(
  unreadByIntent: Record<string, number>,
  intent: string,
  currentIntent: string
): Record<string, number> {
  if (intent === currentIntent) return unreadByIntent
  return { ...unreadByIntent, [intent]: (unreadByIntent[intent] || 0) + 1 }
}
