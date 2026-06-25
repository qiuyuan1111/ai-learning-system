import React, { useEffect, useRef, useState } from 'react'
import { Input, Button, Space, Badge, Radio, Typography, Empty, message } from 'antd'
import { SendOutlined, InfoCircleOutlined, MessageOutlined } from '@ant-design/icons'
import { useAppState } from '../stores'
import { wsClient } from '../services/ws'
import MessageBubble from '../components/chat/MessageBubble'

const { Text, Title } = Typography

export const Chat: React.FC = () => {
  const token = useAppState((state) => state.token)
  const messages = useAppState((state) => state.messages)
  const addMessage = useAppState((state) => state.addMessage)
  const setMessages = useAppState((state) => state.setMessages)
  
  const isConnected = useAppState((state) => state.isConnected)
  const setConnected = useAppState((state) => state.setConnected)
  const isProcessing = useAppState((state) => state.isProcessing)
  const setProcessing = useAppState((state) => state.setProcessing)
  
  const currentIntent = useAppState((state) => state.currentIntent)
  const setCurrentIntent = useAppState((state) => state.setCurrentIntent)

  const [inputText, setInputText] = useState('')
  const [wsStatus, setWsStatus] = useState<'CONNECTING' | 'OPEN' | 'CLOSING' | 'CLOSED'>('CLOSED')
  
  const chatEndRef = useRef<HTMLDivElement>(null)

  // 1. Establish WebSocket connection on mount
  useEffect(() => {
    if (token) {
      wsClient.connect(token)

      // Listen for socket status changes
      const unsubStatus = wsClient.onStatusChange((status) => {
        setWsStatus(status)
        setConnected(status === 'OPEN')
      })

      // Listen for incoming messages
      const unsubMsg = wsClient.onMessage((msg) => {
        addMessage(msg)
        
        // Turn off processing animation when done, error, or single-frame profile_build text is received
        if (
          msg.type === 'done' ||
          msg.type === 'error' ||
          (msg.intent === 'profile_build' && msg.type === 'text')
        ) {
          setProcessing(false)
        }

        // Check if user completed the knowledge profile onboarding
        if (msg.intent === 'profile_build') {
          const contentText = (msg.content as any)?.markdown || ''
          if (contentText.includes('画像已经收集完成') || contentText.includes('画像收集完成')) {
            const currentProfile = useAppState.getState().profile
            if (currentProfile && currentProfile.stage === 'init') {
              const updatedProfile = { ...currentProfile, stage: 'completed' }
              useAppState.getState().setSession(
                useAppState.getState().sessionId!,
                useAppState.getState().token!,
                updatedProfile
              )
              message.success('🎉 学科画像构建完成！您的个性化学习路径和资源已成功解锁。')
            }
          }
        }
      })

      return () => {
        unsubStatus()
        unsubMsg()
        wsClient.disconnect()
      }
    }
  }, [token, addMessage, setConnected, setProcessing])

  // 2. Auto-scroll to bottom of chat
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: isProcessing ? 'auto' : 'smooth' })
  }, [messages, isProcessing])

  // 3. Send Message function
  const handleSend = () => {
    if (!inputText.trim()) return
    if (!isConnected) {
      message.warning('连接已断开，请等待网络重新连接')
      return
    }

    // Add user message to state
    const userMsgId = 'user_' + Math.random().toString(36).substr(2, 9)
    const userMsg = {
      msgId: userMsgId,
      sender: 'user' as const,
      content: inputText,
    }

    // Insert user bubble into messages list
    setMessages([...messages, userMsg as any])
    
    // Set processing state to true
    setProcessing(true)

    // Send via WebSocket Client
    wsClient.send(currentIntent, inputText)

    setInputText('')
  }

  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  // Get status color for status indicator badge
  const getStatusBadge = () => {
    switch (wsStatus) {
      case 'OPEN':
        return <Badge status="success" text="网关连接成功" />
      case 'CONNECTING':
        return <Badge status="processing" text="网关连接中..." style={{ color: '#faad14' }} />
      case 'CLOSED':
      case 'CLOSING':
      default:
        return <Badge status="error" text="网关连接已断开" />
    }
  }

  // Descriptions of intents to help student choose
  const getIntentDesc = () => {
    switch (currentIntent) {
      case 'profile_build':
        return '画像智能体：分析你的知识背景，帮你定制个性化教育档案。'
      case 'tutoring':
        return '辅导智能体：为你提供课程概念的深入问答和学习辅导。'
      case 'evaluate':
        return '评估智能体：针对各科目进行小测与出题，评估当前知识掌握情况。'
      case 'resource_generate':
        return '资源生成智能体：为当前课程生成专属于你的大纲、脑图、PPT和练习册。'
      case 'path_query':
        return '路径规划智能体：查询并动态优化你的专业学习主路径图。'
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 120px)' }}>
      {/* 1. Header Toolbar */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          paddingBottom: '16px',
          borderBottom: '1px solid var(--sidebar-border)',
          marginBottom: '16px',
        }}
      >
        <Space direction="vertical" size={2}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <Title level={4} style={{ margin: 0, fontWeight: 700 }}>
              AI 智能多智能体学习助手
            </Title>
            {getStatusBadge()}
          </div>
          <Text type="secondary" style={{ fontSize: '13px', display: 'inline-flex', alignItems: 'center', gap: 6 }}>
            <InfoCircleOutlined style={{ fontSize: '12px' }} /> {getIntentDesc()}
          </Text>
        </Space>
      </div>

      {/* 2. Intent Selector */}
      <div style={{ marginBottom: '16px', textAlign: 'center' }}>
        <Radio.Group
          value={currentIntent}
          onChange={(e) => setCurrentIntent(e.target.value)}
          buttonStyle="solid"
          size="middle"
        >
          <Radio.Button value="profile_build">👥 知识画像</Radio.Button>
          <Radio.Button value="tutoring">📚 学习答疑</Radio.Button>
          <Radio.Button value="evaluate">✍️ 评估测试</Radio.Button>
          <Radio.Button value="resource_generate">🚀 资源生成</Radio.Button>
          <Radio.Button value="path_query">🗺️ 路径优化</Radio.Button>
        </Radio.Group>
      </div>

      {/* 3. Messages List Area */}
      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: '16px',
          background: 'var(--chat-bg)',
          borderRadius: '12px',
          border: '1px solid var(--glass-border)',
          backdropFilter: 'blur(8px)',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        {messages.length === 0 ? (
          <div style={{ margin: 'auto', textAlign: 'center' }}>
            <Empty
              image={<MessageOutlined style={{ fontSize: '48px', color: '#bfbfbf' }} />}
              description={
                <Space direction="vertical" size="small">
                  <Text type="secondary" style={{ fontWeight: 500, fontSize: '16px' }}>
                    开启一次智能学习会话
                  </Text>
                  <Text type="secondary" style={{ fontSize: '13px' }}>
                    在下方输入框中输入你的问题，选择不同意图，与相应的 AI 智能体对话吧。
                  </Text>
                </Space>
              }
            />
          </div>
        ) : (
          messages.map((msg) => <MessageBubble key={msg.msgId} message={msg} />)
        )}
        
        {/* Loading/Typing Indicator */}
        {isProcessing && (
          <div style={{ display: 'flex', justifyContent: 'flex-start', marginBottom: '20px' }}>
            <Badge status="processing" text="AI 正在思考并生成中..." style={{ color: '#722ed1', fontWeight: 500 }} />
          </div>
        )}
        <div ref={chatEndRef} />
      </div>

      {/* 4. Footer Input Box */}
      <div style={{ marginTop: '16px', display: 'flex', gap: '12px' }}>
        <Input.TextArea
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          onKeyDown={handleKeyPress}
          placeholder={isConnected ? "输入你的学习诉求，按 Enter 键发送..." : "网关未连接，请稍后..."}
          disabled={!isConnected}
          autoSize={{ minRows: 2, maxRows: 4 }}
          style={{
            borderRadius: '8px',
            resize: 'none',
            fontSize: '14px',
            border: '1px solid var(--input-border)',
            background: 'var(--input-bg)',
            color: 'var(--text-color)',
          }}
        />
        <Button
          type="primary"
          icon={<SendOutlined />}
          onClick={handleSend}
          disabled={!inputText.trim() || !isConnected}
          style={{
            height: 'auto',
            width: '80px',
            borderRadius: '8px',
            background: 'linear-gradient(135deg, #1890ff 0%, #722ed1 100%)',
            border: 'none',
            fontWeight: 600,
          }}
        >
          发送
        </Button>
      </div>
    </div>
  )
}

export default Chat
