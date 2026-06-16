import React, { useState } from 'react'
import { Card, Form, Input, Button, Typography, Space, message } from 'antd'
import { useNavigate } from 'react-router-dom'
import { RocketOutlined, SunOutlined, MoonOutlined } from '@ant-design/icons'
import { createSession } from '../services/apiServices'
import { useAppState } from '../stores'

const { Title, Paragraph, Text } = Typography

export const SessionCreate: React.FC = () => {
  const navigate = useNavigate()
  const setSession = useAppState((state) => state.setSession)
  const currentTheme = useAppState((state) => state.theme)
  const toggleTheme = useAppState((state) => state.toggleTheme)
  const [loading, setLoading] = useState(false)

  const onFinish = async (values: { nickname: string; major: string; grade: string }) => {
    setLoading(true)
    try {
      const response = await createSession(values)
      setSession(response.sessionId, response.token, response.profile)
      message.success('学习会话开启成功！')
      navigate('/chat')
    } catch (error: any) {
      console.error(error)
      message.error(error.message || '开启会话失败，请检查网关服务是否正常启动')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '100vh',
        position: 'relative',
        overflow: 'hidden',
        padding: '24px',
      }}
    >
      {/* Floating Theme Switcher in the top right */}
      <div style={{ position: 'absolute', top: '24px', right: '24px', zIndex: 10 }}>
        <button
          className="theme-toggle-btn"
          onClick={toggleTheme}
          title={currentTheme === 'dark' ? '切换为白天模式' : '切换为夜间模式'}
          type="button"
        >
          {currentTheme === 'dark' ? <SunOutlined /> : <MoonOutlined />}
        </button>
      </div>

      {/* Background Neon Blobs */}
      <div className="glow-bg">
        <div className="glow-blob-1" />
        <div className="glow-blob-2" />
      </div>

      <Card
        className="glass-panel"
        style={{
          width: '100%',
          maxWidth: '460px',
          borderRadius: '16px',
        }}
        styles={{ body: { padding: '40px 32px' } }}
      >
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          {/* Header */}
          <div style={{ textAlign: 'center' }}>
            <div
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                width: '64px',
                height: '64px',
                borderRadius: '16px',
                background: 'linear-gradient(135deg, #1890ff 0%, #722ed1 100%)',
                marginBottom: '16px',
                boxShadow: '0 8px 20px rgba(24, 144, 255, 0.4)',
              }}
            >
              <RocketOutlined style={{ fontSize: '32px', color: '#fff' }} />
            </div>
            <Title level={2} style={{ color: 'var(--text-color)', margin: '0 0 8px 0', fontWeight: 700 }}>
              AI 个性化学习辅导系统
            </Title>
            <Paragraph style={{ color: 'var(--text-secondary)', margin: 0 }}>
              构建你的专属知识画像，探索定制化的学习路径与资源生成
            </Paragraph>
          </div>

          {/* Form */}
          <Form layout="vertical" onFinish={onFinish} requiredMark={false}>
            <Form.Item
              name="nickname"
              label={<span style={{ color: 'var(--text-color)', opacity: 0.85, fontWeight: 500 }}>你的昵称</span>}
              rules={[{ required: true, message: '请输入昵称' }]}
            >
              <Input
                placeholder="例如：张三"
                size="large"
                style={{
                  background: 'var(--input-bg)',
                  border: '1px solid var(--input-border)',
                  color: 'var(--text-color)',
                  borderRadius: '8px',
                }}
              />
            </Form.Item>

            <Form.Item
              name="major"
              label={<span style={{ color: 'var(--text-color)', opacity: 0.85, fontWeight: 500 }}>专业名称</span>}
              rules={[{ required: true, message: '请输入专业名称' }]}
            >
              <Input
                placeholder="例如：计算机科学与技术"
                size="large"
                style={{
                  background: 'var(--input-bg)',
                  border: '1px solid var(--input-border)',
                  color: 'var(--text-color)',
                  borderRadius: '8px',
                }}
              />
            </Form.Item>

            <Form.Item
              name="grade"
              label={<span style={{ color: 'var(--text-color)', opacity: 0.85, fontWeight: 500 }}>年级</span>}
              rules={[{ required: true, message: '请输入年级' }]}
            >
              <Input
                placeholder="例如：大三"
                size="large"
                style={{
                  background: 'var(--input-bg)',
                  border: '1px solid var(--input-border)',
                  color: 'var(--text-color)',
                  borderRadius: '8px',
                }}
              />
            </Form.Item>

            <Form.Item style={{ margin: '32px 0 0 0' }}>
              <Button
                type="primary"
                htmlType="submit"
                size="large"
                block
                loading={loading}
                style={{
                  background: 'linear-gradient(135deg, #1890ff 0%, #722ed1 100%)',
                  border: 'none',
                  borderRadius: '8px',
                  fontWeight: 600,
                  height: '46px',
                  boxShadow: '0 4px 12px rgba(114, 46, 209, 0.4)',
                }}
              >
                开启学习会话
              </Button>
            </Form.Item>
          </Form>

          {/* Footer Notice */}
          <div style={{ textAlign: 'center' }}>
            <Text style={{ color: 'var(--text-tertiary)', fontSize: '12px' }}>
              第十五届中国软件杯大赛 A3 赛题项目样例
            </Text>
          </div>
        </Space>
      </Card>
    </div>
  )
}

export default SessionCreate
