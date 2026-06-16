import React from 'react'
import { Avatar, Space, Typography, Alert } from 'antd'
import { UserOutlined, RobotOutlined } from '@ant-design/icons'
import ReactMarkdown from 'react-markdown'
import remarkMath from 'remark-math'
import rehypeKatex from 'rehype-katex'
import type { ServerMessage, ResourceCard as ResourceCardType, ProgressContent, ErrorContent } from '../../types'
import { ResourceCard } from './ResourceCard'
import { ProgressBar } from './ProgressBar'

const { Text } = Typography

interface MessageBubbleProps {
  message: ServerMessage | { msgId: string; sender: 'user'; content: string }
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
  // Check if it's a user message
  const isUser = 'sender' in message && message.sender === 'user'

  // If it's a server done message without text content, hide the entire bubble (including avatar)
  if (!isUser) {
    const assistantMsg = message as ServerMessage
    if (assistantMsg.type === 'done' && !(assistantMsg.content as any)?.markdown) {
      return null
    }
  }

  const renderContent = () => {
    if (isUser) {
      return (
        <div
          style={{
            background: 'linear-gradient(135deg, #1890ff 0%, #722ed1 100%)',
            color: '#fff',
            padding: '12px 18px',
            borderRadius: '16px 4px 16px 16px',
            boxShadow: '0 4px 12px rgba(114, 46, 209, 0.15)',
            maxWidth: '100%',
            wordBreak: 'break-word',
          }}
        >
          <Text style={{ color: '#fff', fontSize: '15px' }}>
            {(message as any).content}
          </Text>
        </div>
      )
    }

    const assistantMsg = message as ServerMessage
    
    switch (assistantMsg.type) {
      case 'text':
      case 'done': {
        const textContent = assistantMsg.content as { markdown: string }
        if (!textContent || !textContent.markdown) return null
        return (
          <div
            style={{
              background: 'var(--glass-bg)',
              color: 'var(--text-color)',
              border: '1px solid var(--glass-border)',
              backdropFilter: 'blur(10px)',
              padding: '12px 18px',
              borderRadius: '4px 16px 16px 16px',
              maxWidth: '100%',
              fontSize: '15px',
              lineHeight: 1.6,
            }}
            className="markdown-body-custom"
          >
            <ReactMarkdown
              remarkPlugins={[remarkMath]}
              rehypePlugins={[rehypeKatex]}
            >
              {textContent.markdown}
            </ReactMarkdown>
          </div>
        )
      }
      
      case 'resource_card': {
        const cardContent = assistantMsg.content as ResourceCardType
        return <ResourceCard card={cardContent} />
      }

      case 'progress': {
        const progressContent = assistantMsg.content as ProgressContent
        return (
          <ProgressBar
            taskId={progressContent.taskId}
            progress={progressContent.progress}
            description={progressContent.description}
          />
        )
      }

      case 'error': {
        const errorContent = assistantMsg.content as ErrorContent
        return (
          <Alert
            message="发生错误"
            description={errorContent.message || '网络连接或后端智能体服务出现故障，请重试。'}
            type="error"
            showIcon
            style={{ borderRadius: '12px', marginTop: '8px' }}
          />
        )
      }

      default:
        return null
    }
  }

  return (
    <div
      style={{
        display: 'flex',
        justifyContent: isUser ? 'flex-end' : 'flex-start',
        marginBottom: '20px',
        width: '100%',
      }}
    >
      <Space
        align="start"
        size="middle"
        style={{
          flexDirection: isUser ? 'row-reverse' : 'row',
          maxWidth: '80%',
        }}
      >
        <Avatar
          size="large"
          icon={isUser ? <UserOutlined /> : <RobotOutlined />}
          style={{
            backgroundColor: isUser ? '#1890ff' : '#722ed1',
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
            flexShrink: 0,
          }}
        />
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: isUser ? 'flex-end' : 'flex-start' }}>
          {renderContent()}
        </div>
      </Space>
    </div>
  )
}

export default MessageBubble
