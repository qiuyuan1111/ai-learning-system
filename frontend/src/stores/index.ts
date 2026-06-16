import { create } from 'zustand'
import type { ServerMessage, TaskResponse } from '../types'

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
  messages: ServerMessage[]
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
  setMessages: (messages: ServerMessage[]) => void
  setConnected: (status: boolean) => void
  setProcessing: (status: boolean) => void
  setCurrentIntent: (intent: AppState['currentIntent']) => void
  updateTask: (taskId: string, task: TaskResponse) => void
  removeTask: (taskId: string) => void
  toggleTheme: () => void
}

export const useAppState = create<AppState>((set) => ({
  // 初始值从 localStorage 恢复
  sessionId: localStorage.getItem('sessionId'),
  token: localStorage.getItem('token'),
  profile: localStorage.getItem('profile') ? JSON.parse(localStorage.getItem('profile')!) : null,
  theme: (localStorage.getItem('theme') as 'light' | 'dark') || 'dark',

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
    set({ sessionId: null, token: null, profile: null, messages: [], activeTasks: {} })
  },

  addMessage: (message) => {
    set((state) => {
      // 避免重复的消息 msgId
      const exists = state.messages.some((m) => m.msgId === message.msgId)
      if (exists) {
        return {
          messages: state.messages.map((m) => (m.msgId === message.msgId ? message : m)),
        }
      }
      return { messages: [...state.messages, message] }
    })
  },

  setMessages: (messages) => set({ messages }),

  setConnected: (status) => set({ isConnected: status }),

  setProcessing: (status) => set({ isProcessing: status }),

  setCurrentIntent: (intent) => set({ currentIntent: intent }),

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
