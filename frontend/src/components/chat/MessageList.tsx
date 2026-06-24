import React, { useEffect, useRef } from 'react'
import { Badge, Empty, Space, Typography } from 'antd'
import { MessageOutlined } from '@ant-design/icons'
import { useAppState } from '../../stores'
import MessageBubble from './MessageBubble'

const { Text } = Typography

interface MessageListProps {
  isProcessing: boolean
}

/**
 * 当前对话 agent 的消息区。
 * 数据源：store.messagesByIntent[currentIntent]（每个对话 agent 独立分区，切换不丢上下文）。
 */
export const MessageList: React.FC<MessageListProps> = ({ isProcessing }) => {
  const currentIntent = useAppState((state) => state.currentIntent)
  const profile = useAppState((state) => state.profile)
  const messages = useAppState((state) => state.messages)

  const chatEndRef = useRef<HTMLDivElement>(null)
  const profileReady = profile?.stage === 'completed'

  // 自动滚动到底部
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: isProcessing ? 'auto' : 'smooth' })
  }, [messages, isProcessing])

  return (
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
                {currentIntent === 'profile_build' ? (
                  <>
                    <Text type="secondary" style={{ fontWeight: 600, fontSize: '16px' }}>
                      第 1 步 · 先认识你 👇
                    </Text>
                    <Text type="secondary" style={{ fontSize: '13px' }}>
                      和我聊聊你的学习背景：专业、年级、想学什么、目前觉得哪里难。
                      其他能力随时可用，但完成画像后体验会更个性化。
                    </Text>
                  </>
                ) : (
                  <>
                    <Text type="secondary" style={{ fontWeight: 500, fontSize: '16px' }}>
                      {currentIntent === 'tutoring' ? '智能答疑已就绪' : '开始对话'}
                    </Text>
                    <Text type="secondary" style={{ fontSize: '13px' }}>
                      {currentIntent === 'tutoring'
                        ? profileReady
                          ? '随时问我课程概念，我会结合你的画像作答，并把你暴露的薄弱点回写到画像。'
                          : '随时可以提问；完成画像后，回答会更贴合你的基础。'
                        : '输入你的需求，按 Enter 发送。'}
                    </Text>
                  </>
                )}
              </Space>
            }
          />
        </div>
      ) : (
        messages.map((msg) => <MessageBubble key={msg.msgId} message={msg as any} />)
      )}

      {/* Loading / Typing 指示 */}
      {isProcessing && (
        <div style={{ display: 'flex', justifyContent: 'flex-start', marginBottom: '20px' }}>
          <Badge status="processing" text="AI 正在思考并生成中..." style={{ color: '#722ed1', fontWeight: 500 }} />
        </div>
      )}
      <div ref={chatEndRef} />
    </div>
  )
}

export default MessageList
