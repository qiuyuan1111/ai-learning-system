import React from 'react'
import { Navigate } from 'react-router-dom'
import { useAppState } from '../stores'

interface ProtectedRouteProps {
  children: React.ReactElement
}

/**
 * 路由保护组件：未登录（没有 token）时重定向到会话创建页面 `/`
 */
export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const token = useAppState((state) => state.token)
  
  if (!token) {
    return <Navigate to="/" replace />
  }

  return children
}

/**
 * 访客路由组件：已登录时直接跳转到聊天界面 `/chat`
 */
export const GuestRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const token = useAppState((state) => state.token)

  if (token) {
    return <Navigate to="/chat" replace />
  }

  return children
}
