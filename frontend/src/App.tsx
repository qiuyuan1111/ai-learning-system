import React, { useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { ConfigProvider, theme } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import { GuestRoute, ProtectedRoute } from './router'
import MainLayout from './layouts/MainLayout'
import SessionCreate from './pages/SessionCreate'
import Chat from './pages/Chat'
import ResourceLibrary from './pages/ResourceLibrary'
import LearningPath from './pages/LearningPath'
import EvaluationReport from './pages/EvaluationReport'
import { useAppState } from './stores'

export const App: React.FC = () => {
  const currentTheme = useAppState((state) => state.theme)

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', currentTheme)
  }, [currentTheme])

  return (
    <ConfigProvider
      locale={zhCN}
      theme={{
        algorithm: currentTheme === 'dark' ? theme.darkAlgorithm : theme.defaultAlgorithm,
        token: {
          colorPrimary: '#1890ff',
          borderRadius: 8,
        },
      }}
    >
      <BrowserRouter>
        <Routes>
          {/* Guest Page: Session Creation */}
          <Route
            path="/"
            element={
              <GuestRoute>
                <SessionCreate />
              </GuestRoute>
            }
          />

          {/* Protected Pages under Sidebar Layout */}
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <MainLayout />
              </ProtectedRoute>
            }
          >
            <Route path="chat" element={<Chat />} />
            <Route path="resources" element={<ResourceLibrary />} />
            <Route path="path" element={<LearningPath />} />
            <Route path="evaluation" element={<EvaluationReport />} />
          </Route>

          {/* Catch-all redirect */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </ConfigProvider>
  )
}

export default App
