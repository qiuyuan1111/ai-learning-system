import React from 'react'
import { Layout, Menu, Button, Avatar, Space, Typography, theme } from 'antd'
import { useNavigate, useLocation, Outlet } from 'react-router-dom'
import {
  MessageOutlined,
  FolderOpenOutlined,
  NodeIndexOutlined,
  BarChartOutlined,
  LogoutOutlined,
  UserOutlined,
  SunOutlined,
  MoonOutlined
} from '@ant-design/icons'
import { useAppState } from '../stores'

const { Sider, Content } = Layout
const { Title, Text } = Typography

export const MainLayout: React.FC = () => {
  const navigate = useNavigate()
  const location = useLocation()
  const profile = useAppState((state) => state.profile)
  const clearSession = useAppState((state) => state.clearSession)
  const currentTheme = useAppState((state) => state.theme)
  const toggleTheme = useAppState((state) => state.toggleTheme)
  
  const {
    token: { borderRadiusLG },
  } = theme.useToken()

  const handleLogout = () => {
    clearSession()
    navigate('/')
  }

  const menuItems = [
    {
      key: '/chat',
      icon: <MessageOutlined style={{ fontSize: '16px' }} />,
      label: '智能学习助手',
    },
    {
      key: '/resources',
      icon: <FolderOpenOutlined style={{ fontSize: '16px' }} />,
      label: '学习资源库',
    },
    {
      key: '/path',
      icon: <NodeIndexOutlined style={{ fontSize: '16px' }} />,
      label: '我的学习路径',
    },
    {
      key: '/evaluation',
      icon: <BarChartOutlined style={{ fontSize: '16px' }} />,
      label: '学习评估报告',
    },
  ]

  return (
    <div style={{ position: 'relative', minHeight: '100vh', overflow: 'hidden' }}>
      {/* Background Neon Blobs */}
      <div className="glow-bg">
        <div className="glow-blob-1" />
        <div className="glow-blob-2" />
      </div>

      <Layout style={{ minHeight: '100vh', background: 'transparent' }}>
        {/* Glassmorphism Sidebar */}
        <Sider
          width={260}
          className="glass-sider"
          style={{
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
          }}
        >
          <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
            {/* Logo Area */}
            <div
              style={{
                padding: '24px 20px',
                display: 'flex',
                alignItems: 'center',
                borderBottom: '1px solid var(--sidebar-border)',
              }}
            >
              <div
                style={{
                  width: 32,
                  height: 32,
                  borderRadius: 10,
                  background: 'linear-gradient(135deg, #1890ff 0%, #722ed1 100%)',
                  marginRight: 12,
                  boxShadow: '0 4px 12px rgba(24, 144, 255, 0.3)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '18px',
                }}
              >
                🤖
              </div>
              <Title level={4} style={{ color: 'var(--text-color)', margin: 0, fontWeight: 700, fontSize: 16, letterSpacing: '0.5px' }}>
                AI Learning System
              </Title>
            </div>

            {/* Navigation Menu */}
            <div style={{ flex: 1, paddingTop: 24 }}>
              <Menu
                theme={currentTheme}
                mode="inline"
                selectedKeys={[location.pathname]}
                onClick={({ key }) => navigate(key)}
                style={{ background: 'transparent', border: 'none' }}
                items={menuItems.map((item) => {
                  const isActive = location.pathname === item.key
                  return {
                    ...item,
                    style: {
                      borderRadius: 8,
                      margin: '6px 16px',
                      width: 'calc(100% - 32px)',
                      background: isActive ? 'linear-gradient(135deg, rgba(24, 144, 255, 0.25) 0%, rgba(114, 46, 209, 0.15) 100%)' : 'transparent',
                      border: isActive ? '1px solid var(--glass-border)' : '1px solid transparent',
                      boxShadow: isActive ? '0 4px 12px rgba(0, 0, 0, 0.05)' : 'none',
                    },
                  }
                })}
              />
            </div>

            {/* User Profile Footer */}
            {profile && (
              <div
                style={{
                  padding: '20px',
                  background: 'transparent',
                  borderTop: '1px solid var(--sidebar-border)',
                }}
              >
                <Space direction="vertical" style={{ width: '100%' }} size="middle">
                  <Space align="center" size="middle">
                    <Avatar
                      size="large"
                      icon={<UserOutlined />}
                      style={{
                        backgroundColor: '#722ed1',
                        boxShadow: '0 2px 10px rgba(114, 46, 209, 0.3)',
                      }}
                    />
                    <div>
                      <Text style={{ color: 'var(--text-color)', fontWeight: 600, display: 'block', fontSize: '14px' }}>
                        {profile.nickname || '学生'}
                      </Text>
                      <Text style={{ color: 'var(--text-secondary)', fontSize: 11, display: 'block', marginTop: '2px' }}>
                        {profile.major} | {profile.grade}
                      </Text>
                    </div>
                  </Space>
                  
                  {/* Theme Switcher Button */}
                  <Button
                    type="text"
                    icon={currentTheme === 'dark' ? <SunOutlined /> : <MoonOutlined />}
                    onClick={toggleTheme}
                    style={{
                      width: '100%',
                      borderRadius: '6px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: 'var(--text-color)',
                      background: 'var(--glass-bg)',
                      border: '1px solid var(--glass-border)',
                    }}
                    onMouseEnter={(e) => {
                      const el = e.currentTarget as HTMLElement
                      el.style.borderColor = '#1890ff'
                      el.style.color = '#1890ff'
                    }}
                    onMouseLeave={(e) => {
                      const el = e.currentTarget as HTMLElement
                      el.style.borderColor = 'var(--glass-border)'
                      el.style.color = 'var(--text-color)'
                    }}
                  >
                    {currentTheme === 'dark' ? '白天模式' : '夜间模式'}
                  </Button>

                  <Button
                    type="text"
                    danger
                    icon={<LogoutOutlined />}
                    onClick={handleLogout}
                    style={{
                      width: '100%',
                      borderRadius: '6px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: 'var(--text-secondary)',
                      background: 'var(--glass-bg)',
                      border: '1px solid var(--glass-border)',
                    }}
                    onMouseEnter={(e) => {
                      const el = e.currentTarget as HTMLElement
                      el.style.color = '#ff4d4f'
                      el.style.background = 'rgba(255, 77, 79, 0.08)'
                      el.style.borderColor = 'rgba(255, 77, 79, 0.2)'
                    }}
                    onMouseLeave={(e) => {
                      const el = e.currentTarget as HTMLElement
                      el.style.color = 'var(--text-secondary)'
                      el.style.background = 'var(--glass-bg)'
                      el.style.borderColor = 'var(--glass-border)'
                    }}
                  >
                    退出会话
                  </Button>
                </Space>
              </div>
            )}
          </div>
        </Sider>

        {/* Main Content Area */}
        <Layout style={{ padding: '0', background: 'transparent' }}>
          <Content
            style={{
              padding: '24px 32px',
              margin: 0,
              minHeight: 280,
              overflowY: 'auto',
            }}
          >
            {/* Glassmorphism content container card */}
            <div
              className="glass-panel"
              style={{
                padding: 30,
                minHeight: '100%',
                borderRadius: borderRadiusLG,
              }}
            >
              <Outlet />
            </div>
          </Content>
        </Layout>
      </Layout>
    </div>
  )
}

export default MainLayout
