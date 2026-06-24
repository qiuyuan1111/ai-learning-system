import React, { useEffect, useRef, useState } from 'react'
import { Space, Badge, Typography, message, Steps } from 'antd'
import { InfoCircleOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { useAppState } from '../stores'
import { wsClient } from '../services/ws'
import MessageList from '../components/chat/MessageList'
import ChatInput from '../components/chat/ChatInput'
import AgentTab from '../components/chat/AgentTab'
import type { DialogueTurn } from '../types'

const { Text, Title } = Typography

// 五阶段学习旅程（顺序即引导顺序）。对话型 agent（画像/答疑）切 currentIntent，
// 其余（资源/路径/评估）跳路由到各自独立页面。
const FLOW_STEPS = [
  { title: '知识画像', intent: 'profile_build', path: '/chat' },
  { title: '学习资源', intent: 'resource_generate', path: '/resources' },
  { title: '学习路径', intent: 'path_query', path: '/path' },
  { title: '智能答疑', intent: 'tutoring', path: '/chat' },
  { title: '能力评估', intent: 'evaluate', path: '/evaluation' },
] as const
const INTENT_TO_STEP: Record<string, number> = {
  profile_build: 0,
  resource_generate: 1,
  path_query: 2,
  tutoring: 3,
  evaluate: 4,
}

export const Chat: React.FC = () => {
  const navigate = useNavigate()
  const token = useAppState((state) => state.token)
  const profile = useAppState((state) => state.profile)
  const setSession = useAppState((state) => state.setSession)
  const addMessage = useAppState((state) => state.addMessage)
  const addUserMessage = useAppState((state) => state.addUserMessage)

  const isConnected = useAppState((state) => state.isConnected)
  const setConnected = useAppState((state) => state.setConnected)
  const isProcessing = useAppState((state) => state.isProcessing)
  const setProcessing = useAppState((state) => state.setProcessing)

  const currentIntent = useAppState((state) => state.currentIntent)
  const setCurrentIntent = useAppState((state) => state.setCurrentIntent)
  const messagesByIntent = useAppState((state) => state.messagesByIntent)

  const profileReady = profile?.stage === 'completed'
  const currentStep = profileReady ? INTENT_TO_STEP[currentIntent] ?? 0 : 0

  const [wsStatus, setWsStatus] = useState<'CONNECTING' | 'OPEN' | 'CLOSING' | 'CLOSED'>('CLOSED')

  // 联动节流：tutor 答疑完成后，攒最近几轮问答 + 30s 去抖，再发 profile_update
  const profileUpdateTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

  // 1. 建立 WebSocket 连接
  useEffect(() => {
    if (!token) return
    wsClient.connect(token)

    const unsubStatus = wsClient.onStatusChange((status) => {
      setWsStatus(status)
      setConnected(status === 'OPEN')
    })

    const unsubMsg = wsClient.onMessage((msg) => {
      addMessage(msg)

      // 关闭处理动画：done / error / 画像单帧 text
      if (
        msg.type === 'done' ||
        msg.type === 'error' ||
        (msg.intent === 'profile_build' && msg.type === 'text')
      ) {
        setProcessing(false)
      }

      // 画像构建完成（done 帧）：解锁后续
      if (msg.intent === 'profile_build' && msg.type === 'done') {
        const cur = useAppState.getState().profile
        if (cur && cur.stage === 'init') {
          setSession(useAppState.getState().sessionId!, useAppState.getState().token!, {
            ...cur,
            stage: 'completed',
          })
          message.success('🎉 学科画像构建完成！资源、路径、评估已为你解锁。')
        }
      }

      // 画像动态更新（联动回帧）：刷新 store.profile（version 推进）
      if (msg.intent === 'profile_build' && msg.type === 'text' && (msg.content as any)?.version) {
        const cur = useAppState.getState().profile
        if (cur) {
          setSession(useAppState.getState().sessionId!, useAppState.getState().token!, {
            ...cur,
            version: (msg.content as any).version,
          })
        }
      }

      // 联动触发：tutor 答疑完成 → 攒问答 → 30s 去抖发 profile_update
      if (msg.intent === 'tutoring' && msg.type === 'done') {
        scheduleProfileUpdate()
      }
    })

    return () => {
      unsubStatus()
      unsubMsg()
      wsClient.disconnect()
      if (profileUpdateTimer.current) clearTimeout(profileUpdateTimer.current)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token, addMessage, setConnected, setProcessing])

  // 从 tutoring 分区提取最近 N 轮问答（user question + assistant markdown），组 dialogue
  const buildRecentDialogue = (turns = 3): DialogueTurn[] => {
    const tutorMsgs = messagesByIntent['tutoring'] || []
    const dialogue: DialogueTurn[] = []
    // 倒序找最近 turns 个 user 气泡，配对其后的 assistant text
    for (let i = tutorMsgs.length - 1; i >= 0 && dialogue.length / 2 < turns; i--) {
      const m = tutorMsgs[i] as any
      if ('sender' in m && m.sender === 'user') {
        dialogue.unshift({ role: 'user', content: m.content })
        // 找该 user 之后第一条 assistant text
        for (let j = i + 1; j < tutorMsgs.length; j++) {
          const a = tutorMsgs[j] as any
          if (!('sender' in a) && a.type === 'text') {
            dialogue.unshift({ role: 'assistant', content: (a.content as any)?.markdown || '' })
            break
          }
        }
      }
    }
    // 保证 user/assistant 成对，过滤孤儿
    const paired: DialogueTurn[] = []
    for (let i = 0; i + 1 < dialogue.length; i += 2) {
      if (dialogue[i].role === 'assistant' && dialogue[i + 1].role === 'user') {
        paired.push(dialogue[i + 1], dialogue[i])
      }
    }
    return paired.slice(-turns * 2)
  }

  // 30s 去抖：避免每答一题就触发一次画像更新
  const scheduleProfileUpdate = () => {
    if (!profileReady) return // 画像未建好前不联动
    if (profileUpdateTimer.current) clearTimeout(profileUpdateTimer.current)
    profileUpdateTimer.current = setTimeout(() => {
      const dialogue = buildRecentDialogue(3)
      if (dialogue.length === 0) return
      wsClient.send('profile_update', '', { dialogue })
    }, 30000)
  }

  // 2. 发送消息
  const handleSend = (text: string) => {
    if (!text.trim()) return
    if (!isConnected) {
      message.warning('连接已断开，请等待网络重新连接')
      return
    }

    addUserMessage(currentIntent, text)
    setProcessing(true)
    wsClient.send(currentIntent, text)
  }

  // 流程条点击：软引导，全部可点（不再锁定）
  const onStepClick = (i: number) => {
    const step = FLOW_STEPS[i]
    if (step.intent === 'profile_build' || step.intent === 'tutoring') {
      setCurrentIntent(step.intent)
    } else {
      navigate(step.path)
    }
  }

  const getStatusBadge = () => {
    switch (wsStatus) {
      case 'OPEN':
        return <Badge status="success" text="网关连接成功" />
      case 'CONNECTING':
        return <Badge status="processing" text="网关连接中..." style={{ color: '#faad14' }} />
      default:
        return <Badge status="error" text="网关连接已断开" />
    }
  }

  const getIntentDesc = () => {
    switch (currentIntent) {
      case 'profile_build':
        return '画像智能体：分析你的知识背景，帮你定制个性化教育档案。'
      case 'tutoring':
        return '辅导智能体：为你提供课程概念的深入问答和学习辅导，并把你的薄弱点回写到画像。'
      default:
        return '选择上方能力，开始个性化学习。'
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

      {/* 2. 引导式流程条：五阶段学习旅程（软引导，未完成画像仅灰显不锁定） */}
      <div style={{ marginBottom: '16px' }}>
        <Steps
          size="small"
          current={currentStep}
          onChange={onStepClick}
          items={FLOW_STEPS.map((s) => ({ title: s.title }))}
        />
      </div>

      {/* 3. 功能切换条：按学习旅程 ①~⑤ 排列，与上方 Steps 完全对齐。
            画像/答疑是对话型（切 currentIntent，独立消息分区）；资源/路径/评估跳路由。 */}
      <div style={{ marginBottom: '16px', textAlign: 'center' }}>
        <Space size="middle">
          <AgentTab
            active={currentIntent === 'profile_build'}
            onClick={() => setCurrentIntent('profile_build')}
          >
            ① 知识画像
          </AgentTab>
          <AgentTab onClick={() => navigate('/resources')} dim={!profileReady}>
            ② 学习资源
          </AgentTab>
          <AgentTab onClick={() => navigate('/path')} dim={!profileReady}>
            ③ 学习路径
          </AgentTab>
          <AgentTab
            active={currentIntent === 'tutoring'}
            onClick={() => setCurrentIntent('tutoring')}
            dim={!profileReady}
          >
            ④ 智能答疑
          </AgentTab>
          <AgentTab onClick={() => navigate('/evaluation')} dim={!profileReady}>
            ⑤ 能力评估
          </AgentTab>
        </Space>
      </div>

      {/* 4. 消息区（当前对话 agent 的独立分区） */}
      <MessageList isProcessing={isProcessing} />

      {/* 5. 输入框（仅网络断开禁用，不再因画像未完成禁用） */}
      <ChatInput isConnected={isConnected} onSend={handleSend} />
    </div>
  )
}

export default Chat
