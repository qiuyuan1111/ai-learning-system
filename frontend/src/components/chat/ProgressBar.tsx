import React, { useEffect, useRef } from 'react'
import { Progress, Space, Typography } from 'antd'
import { LoadingOutlined, CheckCircleOutlined, CloseCircleOutlined } from '@ant-design/icons'
import { useAppState } from '../../stores'
import { getTaskStatus } from '../../services/apiServices'

const { Text } = Typography

interface ProgressBarProps {
  taskId: string
  progress: number
  description: string
}

export const ProgressBar: React.FC<ProgressBarProps> = ({ taskId, progress, description }) => {
  const updateTask = useAppState((state) => state.updateTask)
  const addMessage = useAppState((state) => state.addMessage)
  const activeTasks = useAppState((state) => state.activeTasks)
  
  const timerRef = useRef<any>(null)

  useEffect(() => {
    const task = activeTasks[taskId]
    const isRunning = !task || (task.status !== 'completed' && task.status !== 'failed')

    if (isRunning && progress < 100) {
      // Start polling every 3 seconds
      timerRef.current = setInterval(async () => {
        try {
          const taskData = await getTaskStatus(taskId)
          updateTask(taskId, taskData)

          // If completed, add resource cards to the message stream
          if (taskData.status === 'completed' && taskData.result?.resources) {
            clearInterval(timerRef.current)
            
            // Add a text indicating generation completed
            addMessage({
              msgId: `text_done_${taskId}`,
              replyTo: '',
              intent: 'resource_generate',
              type: 'text',
              content: {
                markdown: `🎉 **个性化学习资源生成完成！** 以下是为你定制的资源：`
              }
            })

            // Add resource cards to chat message list
            taskData.result.resources.forEach((resource, index) => {
              addMessage({
                msgId: `res_${taskId}_${index}`,
                replyTo: '',
                intent: 'resource_generate',
                type: 'resource_card',
                content: {
                  resourceId: resource.resourceId,
                  resourceType: resource.type,
                  title: resource.title,
                  url: resource.url,
                  description: `${resource.title} 的定制化学习内容`
                }
              })
            })
          } else if (taskData.status === 'failed') {
            clearInterval(timerRef.current)
            addMessage({
              msgId: `text_fail_${taskId}`,
              replyTo: '',
              intent: 'resource_generate',
              type: 'error',
              content: {
                code: 500,
                message: '非常抱歉，个性化资源生成失败，请重试。'
              } as any
            })
          }
        } catch (error) {
          console.error('[ProgressBar] Polling failed', error)
        }
      }, 3000)
    }

    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current)
      }
    }
  }, [taskId, progress, activeTasks, updateTask, addMessage])

  const getStatusIcon = () => {
    const task = activeTasks[taskId]
    if (!task) return <LoadingOutlined style={{ color: '#1890ff' }} />
    
    switch (task.status) {
      case 'completed':
        return <CheckCircleOutlined style={{ color: '#52c41a', fontSize: '16px' }} />
      case 'failed':
        return <CloseCircleOutlined style={{ color: '#ff4d4f', fontSize: '16px' }} />
      case 'processing':
      case 'pending':
      default:
        return <LoadingOutlined style={{ color: '#1890ff' }} />
    }
  }

  const getStatusText = () => {
    const task = activeTasks[taskId]
    if (!task) return '排队中...'
    switch (task.status) {
      case 'completed':
        return '生成成功'
      case 'failed':
        return '生成失败'
      case 'processing':
        return '正在生成...'
      case 'pending':
      default:
        return '排队中...'
    }
  }

  return (
    <div
      style={{
        width: '100%',
        maxWidth: '300px',
        padding: '16px',
        background: 'var(--glass-bg)',
        borderRadius: '12px',
        border: '1px solid var(--glass-border)',
        backdropFilter: 'blur(8px)',
        marginTop: '8px',
      }}
    >
      <Space direction="vertical" style={{ width: '100%' }} size="small">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Text style={{ fontSize: '12px', color: 'var(--text-secondary)', fontWeight: 500 }}>
            {getStatusText()}
          </Text>
          {getStatusIcon()}
        </div>
        <Progress
          percent={progress}
          size="small"
          status={activeTasks[taskId]?.status === 'failed' ? 'exception' : progress === 100 ? 'success' : 'active'}
          strokeColor={{
            from: '#1890ff',
            to: '#722ed1',
          }}
        />
        <Text style={{ fontSize: '13px', color: 'var(--text-color)', display: 'block', marginTop: '4px' }}>
          {description}
        </Text>
      </Space>
    </div>
  )
}
export default ProgressBar
