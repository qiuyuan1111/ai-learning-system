import React, { useEffect, useState } from 'react'
import { Card, Timeline, Button, Space, Typography, Badge, message } from 'antd'
import {
  NodeIndexOutlined,
  PlayCircleOutlined,
  CheckCircleOutlined,
  SyncOutlined
} from '@ant-design/icons'
import { getLearningPath, triggerRecommend } from '../services/apiServices'
import { useAppState } from '../stores'
import type { PathNode } from '../types'

const { Title, Paragraph, Text } = Typography

export const LearningPath: React.FC = () => {
  const sessionId = useAppState((state) => state.sessionId)

  const [nodes, setNodes] = useState<PathNode[]>([])
  const [loading, setLoading] = useState(false)
  const [recommending, setRecommending] = useState(false)

  const fetchPath = async () => {
    if (!sessionId) return
    setLoading(true)
    try {
      const response = await getLearningPath(sessionId)
      // Sort nodes by order
      const sortedNodes = (response.nodes || []).sort((a, b) => a.order - b.order)
      setNodes(sortedNodes)
    } catch (error: any) {
      console.error(error)
      message.error(error.message || '获取学习路径失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchPath()
  }, [sessionId])

  const handleRecommend = async () => {
    if (!sessionId) return
    setRecommending(true)
    try {
      await triggerRecommend(sessionId)
      message.success('已成功触发路径重新规划与推荐！正在更新路径节点...')
      // Wait a moment and refresh
      setTimeout(() => {
        fetchPath()
      }, 1500)
    } catch (error: any) {
      console.error(error)
      message.error(error.message || '路径规划失败')
    } finally {
      setRecommending(false)
    }
  }

  const getTimelineDot = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircleOutlined style={{ fontSize: '18px', color: '#52c41a' }} />
      case 'in_progress':
        return <SyncOutlined spin style={{ fontSize: '18px', color: '#1890ff' }} />
      case 'pending':
      default:
        return <Badge status="default" style={{ fontSize: '18px' }} />
    }
  }

  const getTimelineColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'green'
      case 'in_progress':
        return 'blue'
      case 'pending':
      default:
        return 'gray'
    }
  }

  return (
    <div>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div>
          <Title level={3} style={{ margin: 0, fontWeight: 700 }}>
            我的学习路径
          </Title>
          <Paragraph style={{ color: 'var(--text-secondary)', margin: 0 }}>
            系统通过对你的学术画像分析，生成了以下自适应的专属课程学习时间轴。
          </Paragraph>
        </div>
        
        <Button
          type="primary"
          icon={<NodeIndexOutlined />}
          loading={recommending}
          onClick={handleRecommend}
          style={{
            background: 'linear-gradient(135deg, #1890ff 0%, #722ed1 100%)',
            border: 'none',
            borderRadius: '6px',
            fontWeight: 600,
          }}
        >
          重新规划学习路径
        </Button>
      </div>

      {/* Path Timeline Card */}
      <Card
        loading={loading}
        className="glass-panel"
        style={{
          borderRadius: '12px',
        }}
        styles={{ body: { padding: '40px 32px' } }}
      >
        {nodes.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '40px 0' }}>
            <Text type="secondary">目前还没有规划出的学习路径。请尝试点击右上角“重新规划学习路径”进行生成。</Text>
          </div>
        ) : (
          <Timeline
            mode="start"
            items={nodes.map((node) => ({
              color: getTimelineColor(node.status),
              icon: getTimelineDot(node.status),
              children: (
                <div style={{ paddingBottom: '24px', marginLeft: '12px' }}>
                  <Title
                    level={5}
                    style={{
                      margin: '0 0 8px 0',
                      color: node.status === 'pending' ? 'var(--text-tertiary)' : 'var(--text-color)',
                      fontWeight: 650,
                    }}
                  >
                    {node.title}
                  </Title>
                  
                  {node.resource && (
                    <Space size="middle" style={{ marginTop: '4px' }}>
                      <Tag color={node.status === 'completed' ? 'green' : 'blue'}>
                        {node.resource.type.toUpperCase()} 资源已就绪
                      </Tag>
                      <Button
                        type="link"
                        size="small"
                        icon={<PlayCircleOutlined />}
                        href={node.resource.url}
                        target="_blank"
                        style={{ padding: 0 }}
                      >
                        立即开始学习
                      </Button>
                    </Space>
                  )}
                </div>
              ),
            }))}
          />
        )}
      </Card>
    </div>
  )
}

// Simple internal helper Tag component
const Tag: React.FC<{ color: string; children: React.ReactNode }> = ({ color, children }) => {
  return (
    <span
      style={{
        display: 'inline-block',
        padding: '2px 8px',
        fontSize: '11px',
        fontWeight: 600,
        borderRadius: '4px',
        background: color === 'green' ? 'var(--tag-bg-green, rgba(82, 196, 26, 0.1))' : 'var(--tag-bg-blue, rgba(24, 144, 255, 0.1))',
        color: color === 'green' ? 'var(--tag-text-green, #52c41a)' : 'var(--tag-text-blue, #1890ff)',
        border: `1px solid ${color === 'green' ? 'var(--tag-border-green, rgba(82, 196, 26, 0.2))' : 'var(--tag-border-blue, rgba(24, 144, 255, 0.2))'}`,
      }}
    >
      {children}
    </span>
  )
}

export default LearningPath
