import React, { useState } from 'react'
import { Input, Button } from 'antd'
import { SendOutlined } from '@ant-design/icons'

interface ChatInputProps {
  isConnected: boolean
  onSend: (text: string) => void
}

/**
 * 聊天输入框 + 发送按钮。
 * 仅在网络断开时禁用；Enter 发送，Shift+Enter 换行。
 */
export const ChatInput: React.FC<ChatInputProps> = ({ isConnected, onSend }) => {
  const [inputText, setInputText] = useState('')

  const handleSend = () => {
    if (!inputText.trim()) return
    onSend(inputText)
    setInputText('')
  }

  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div style={{ marginTop: '16px', display: 'flex', gap: '12px' }}>
      <Input.TextArea
        value={inputText}
        onChange={(e) => setInputText(e.target.value)}
        onKeyDown={handleKeyPress}
        placeholder={isConnected ? '输入你的学习诉求，按 Enter 键发送...' : '网关未连接，请稍后...'}
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
  )
}

export default ChatInput
