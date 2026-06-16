import { WebSocket } from 'ws'
import { config } from '../config'
import connectionManager from './connection'

// Simple session state tracking for mocks
const profileRounds = new Map<string, number>()

export function handleClientMessage(sessionId: string, data: string): void {
  try {
    const msg = JSON.parse(data)
    const { msgId, intent, content, context } = msg

    console.log(`[WSRouter] Received message from session ${sessionId}: intent=${intent}, text="${content.text}"`)

    if (config.mockMode) {
      handleMockMessage(sessionId, msgId, intent, content.text, context)
    } else {
      // In PROXY mode, connect gateway to B/C services via WebSockets
      handleProxyMessage(sessionId, msg)
    }
  } catch (error) {
    console.error('[WSRouter] Error processing WS client message', error)
  }
}

/**
 * MOCK MODE: Simulate streaming and conversational logic for all intents
 */
function handleMockMessage(
  sessionId: string,
  replyTo: string,
  intent: string,
  text: string,
  context?: any
) {
  const sendText = (markdown: string, type: 'text' | 'done' = 'text') => {
    connectionManager.send(sessionId, {
      msgId: 'server_' + Math.random().toString(36).substr(2, 9),
      replyTo,
      intent,
      type,
      content: { markdown },
    })
  }

  const sendProgress = (taskId: string, progress: number, description: string) => {
    connectionManager.send(sessionId, {
      msgId: 'server_' + Math.random().toString(36).substr(2, 9),
      replyTo,
      intent,
      type: 'progress',
      content: { taskId, progress, description },
    })
  }

  // 1. Profile Builder Intent Flow
  if (intent === 'profile_build') {
    const round = profileRounds.get(sessionId) || 1
    
    if (round === 1) {
      setTimeout(() => {
        sendText('你好！我是画像智能体。为了定制你的专属学习档案，我需要了解你目前的学习状态。')
      }, 500)
      setTimeout(() => {
        sendText('你能先用一句话描述一下你在当前专业方向上，目前最感兴趣的领域、或者学得最吃力的核心知识点吗？', 'done')
        profileRounds.set(sessionId, 2)
      }, 1500)
    } else if (round === 2) {
      setTimeout(() => {
        sendText('收到！了解了你的基本学科背景。接着，我想询问下你的目标：你目前学习这门课是为了应付期末考试、独立完成课程大作业，还是为了日后读研/找工作做技术积累？')
      }, 500)
      setTimeout(() => {
        sendText('明确的目标有助于我更精准地为你裁剪学习重点。', 'done')
        profileRounds.set(sessionId, 3)
      }, 1500)
    } else {
      setTimeout(() => {
        sendText('非常棒！你的基本学科画像已经收集完成。')
      }, 500)
      setTimeout(() => {
        sendText('系统已为你匹配了对应的学习大纲、并正在定制你的学习路径和评估小测。你可以通过上方按钮切换到“学习答疑”或“评估测试”与我进一步沟通，也可以选择“资源生成”为自己定制学习脑图。', 'done')
        profileRounds.set(sessionId, 1) // Reset loop
      }, 1500)
    }
  }

  // 2. Tutoring Answer Intent Flow
  else if (intent === 'tutoring') {
    setTimeout(() => sendText('关于你的问题，我来为你进行详细解答：\n\n'), 200)
    setTimeout(() => {
      sendText('机器学习的本质是利用数学模型拟合数据规律。在线性模型中，我们的目标是拟合一个超平面公式：\n\n$$f(x) = w^T x + b$$\n\n')
    }, 1000)
    setTimeout(() => {
      sendText('为了找到最优的权重向量 $w$，我们定义了均方误差损失函数（MSE）：\n\n$$J(w, b) = \\frac{1}{2m} \\sum_{i=1}^{m} (f(x^{(i)}) - y^{(i)})^2$$\n\n并通过梯度下降迭代来优化参数：\n\n$$\\theta := \\theta - \\alpha \\nabla J(\\theta)$$\n\n')
    }, 2000)
    setTimeout(() => {
      sendText('你可以通过选择「评估测试」模块来检测一下自己对梯度下降以及代价函数的掌握情况。我会随时在右侧为你提供帮助。', 'done')
    }, 3500)
  }

  // 3. Resource Generation Intent Flow (Async simulated background task)
  else if (intent === 'resource_generate') {
    const mockTaskId = 'task_gen_' + Math.random().toString(36).substr(2, 9)
    
    setTimeout(() => sendProgress(mockTaskId, 10, '正在解析专业课件与大纲...'), 200)
    setTimeout(() => sendProgress(mockTaskId, 45, '正在抽取核心概念与知识节点结构...'), 1200)
    setTimeout(() => sendProgress(mockTaskId, 75, '正在排版思维导图及PPT大纲结构...'), 2200)
    setTimeout(() => {
      sendProgress(mockTaskId, 100, '学习资源生成成功，已创建文件实体！')
      // Send a done frame so the user input box is unlocked
      sendText('个性化资源生成任务已成功启动，正在本地磁盘为您生成思维导图和PDF导读文件...', 'done')
    }, 3200)
  }

  // 4. Learning Path Query Flow
  else if (intent === 'path_query') {
    setTimeout(() => {
      sendText('正在查询你的定制化学科主路径树...\n\n你可以通过左侧侧边栏切换到 **「我的学习路径」** 查看可视化的垂直时间线时间轴，其中包括了为你标记的已完成、进行中和待学习的节点。')
    }, 500)
    setTimeout(() => {
      sendText('如有任何节点不理解，可以随时在此向我发送“答疑 [节点名称]”进行学习答疑。', 'done')
    }, 1500)
  }

  // 5. Evaluation test Flow
  else if (intent === 'evaluate') {
    setTimeout(() => {
      sendText('收到评估小测请求！\n\n我们已经为你准备了当前科目的评估测试题。你可以通过左侧的 **「学习评估报告」** 查看你当前的技能雷达图和薄弱知识点分析，以获得进一步的学习建议。', 'done')
    }, 500)
  }
}

/**
 * PROXY MODE: Connect and relay WS messages to actual backend microservices
 */
const backendSockets = new Map<string, WebSocket>()

function handleProxyMessage(sessionId: string, clientMsg: any) {
  const { intent, msgId } = clientMsg

  // Determine target websocket URL based on intent
  let targetUrl = ''
  if (intent === 'profile_build') {
    targetUrl = config.services.profile
  } else if (intent === 'tutoring') {
    targetUrl = config.services.tutor
  } else {
    // For REST backends, we do not have direct WS URLs. 
    // Usually B/C will have standard WS handlers or we return error/REST relay.
    console.error(`[WSRouter] Intent ${intent} is not mapped to a WS target service in PROXY mode`)
    connectionManager.send(sessionId, {
      msgId: 'err_' + msgId,
      replyTo: msgId,
      intent,
      type: 'error',
      content: { code: 400, message: `Intent ${intent} requires REST endpoint forwarding` },
    })
    return
  }

  const socketKey = `${sessionId}_${intent}`
  let backendWs = backendSockets.get(socketKey)

  if (!backendWs || backendWs.readyState !== WebSocket.OPEN) {
    console.log(`[WSRouter] Establishing new WS connection to backend service: ${targetUrl}`)
    
    backendWs = new WebSocket(targetUrl)
    backendSockets.set(socketKey, backendWs)

    backendWs.on('open', () => {
      console.log(`[WSRouter] Backend WS opened. Relaying message: ${msgId}`)
      backendWs!.send(JSON.stringify(clientMsg))
    })

    backendWs.on('message', (data) => {
      console.log(`[WSRouter] Received reply from backend WS: ${intent}`)
      // Relay reply back to the client
      try {
        const parsedReply = JSON.parse(data.toString())
        connectionManager.send(sessionId, parsedReply)
      } catch (err) {
        connectionManager.send(sessionId, data.toString())
      }
    })

    backendWs.on('error', (err) => {
      console.error(`[WSRouter] Backend WS error on intent ${intent}`, err)
      connectionManager.send(sessionId, {
        msgId: 'err_' + msgId,
        replyTo: msgId,
        intent,
        type: 'error',
        content: { code: 502, message: `Backend service at ${targetUrl} threw an error` },
      })
    })

    backendWs.on('close', () => {
      console.log(`[WSRouter] Backend WS closed for session: ${sessionId}`)
      backendSockets.delete(socketKey)
    })
  } else {
    // Relaying directly if already open
    backendWs.send(JSON.stringify(clientMsg))
  }
}
