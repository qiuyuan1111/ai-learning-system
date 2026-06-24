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

  // 6. Profile Update Flow（联动：tutor 答疑后动态更新画像，Mock 直接回更新确认）
  else if (intent === 'profile_update') {
    setTimeout(() => {
      connectionManager.send(sessionId, {
        msgId: 'server_' + Math.random().toString(36).substr(2, 9),
        replyTo,
        intent: 'profile_build',
        type: 'text',
        content: { markdown: '画像已更新', version: Date.now() % 100 },
      })
    }, 300)
  }
}

/**
 * PROXY MODE: Connect and relay WS messages to actual backend microservices
 */
const backendSockets = new Map<string, WebSocket>()

function handleProxyMessage(sessionId: string, clientMsg: any) {
  const { intent, msgId, content } = clientMsg
  const text = content?.text || ''

  // 1) profile_build / profile_update / tutoring → B 的 WS 服务（profile/tutor 的 /ws/chat），直接转发
  if (intent === 'profile_build' || intent === 'profile_update' || intent === 'tutoring') {
    relayToBackendWs(sessionId, clientMsg)
    return
  }

  // 2) resource_generate → C 的 resource-gen（REST）：触发异步生成 + 轮询进度推回
  if (intent === 'resource_generate') {
    void bridgeResourceGenerate(sessionId, msgId, text, clientMsg.context)
    return
  }

  // 3) path_query → C 的 path-planner（REST）：GET 触发/确认路径，回引导帧
  if (intent === 'path_query') {
    void bridgePathQuery(sessionId, msgId, text)
    return
  }

  // 4) evaluate → B 的 evaluator（REST）：答题数据走 REST submit/report，WS 仅回引导帧
  if (intent === 'evaluate') {
    sendText(
      sessionId,
      msgId,
      'evaluate',
      '收到评估请求。请完成测验题目后提交，系统将生成评估报告；可在「学习评估报告」查看雷达图与薄弱点分析。',
      'done'
    )
    return
  }

  console.error(`[WSRouter] Unknown intent in PROXY mode: ${intent}`)
  connectionManager.send(sessionId, {
    msgId: 'err_' + msgId,
    replyTo: msgId,
    intent,
    type: 'error',
    content: { code: 400, message: `Unknown intent: ${intent}` },
  })
}

// ── WS 转发：profile_build / profile_update / tutoring（这些后端是真正的 WS 服务）──
function relayToBackendWs(sessionId: string, clientMsg: any) {
  const { intent, msgId } = clientMsg
  // profile_build 与 profile_update 都去 profile 服务；tutoring 去 tutor 服务
  const isProfile = intent === 'profile_build' || intent === 'profile_update'
  const svcUrl = isProfile ? config.services.profile : config.services.tutor
  const base = svcUrl.endsWith('/') ? svcUrl.slice(0, -1) : svcUrl
  const url = base.endsWith('/ws/chat') ? base : `${base}/ws/chat`
  const targetUrl = `${url}?session_id=${encodeURIComponent(sessionId)}`

  // socketKey 按目的地归并：同一 session 对同一后端服务只建一条 WS，
  // 避免 profile_build 与 profile_update 各建一条到 profile 的连接。
  const dest = isProfile ? 'profile' : 'tutor'
  const socketKey = `${sessionId}_${dest}`
  let backendWs = backendSockets.get(socketKey)

  if (!backendWs || backendWs.readyState !== WebSocket.OPEN) {
    console.log(`[WSRouter] Establishing backend WS: ${targetUrl}`)
    backendWs = new WebSocket(targetUrl)
    backendSockets.set(socketKey, backendWs)

    backendWs.on('open', () => {
      console.log(`[WSRouter] Backend WS opened (${intent}). Relaying: ${msgId}`)
      backendWs!.send(JSON.stringify(clientMsg))
    })

    backendWs.on('message', (data) => {
      try {
        connectionManager.send(sessionId, JSON.parse(data.toString()))
      } catch (err) {
        connectionManager.send(sessionId, data.toString())
      }
    })

    backendWs.on('error', (err) => {
      console.error(`[WSRouter] Backend WS error (${intent})`, err)
      connectionManager.send(sessionId, {
        msgId: 'err_' + msgId,
        replyTo: msgId,
        intent,
        type: 'error',
        content: { code: 502, message: `Backend ${intent} service at ${targetUrl} threw an error` },
      })
    })

    backendWs.on('close', () => {
      console.log(`[WSRouter] Backend WS closed (${intent}) session=${sessionId}`)
      backendSockets.delete(socketKey)
    })
  } else {
    backendWs.send(JSON.stringify(clientMsg))
  }
}

// ── WS 帧辅助 ──
function randId(prefix: string): string {
  return prefix + Math.random().toString(36).slice(2, 11)
}

function sendText(
  sessionId: string,
  replyTo: string,
  intent: string,
  markdown: string,
  type: 'text' | 'done' = 'text'
) {
  connectionManager.send(sessionId, {
    msgId: randId('srv_'),
    replyTo,
    intent,
    type,
    content: { markdown },
  })
}

function sendProgress(
  sessionId: string,
  replyTo: string,
  intent: string,
  taskId: string,
  progress: number,
  description: string
) {
  connectionManager.send(sessionId, {
    msgId: randId('srv_'),
    replyTo,
    intent,
    type: 'progress',
    content: { taskId, progress, description },
  })
}

function sendError(sessionId: string, replyTo: string, intent: string, message: string) {
  connectionManager.send(sessionId, {
    msgId: randId('srv_'),
    replyTo,
    intent,
    type: 'error',
    content: { code: 500, message },
  })
}

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms))

function guessResourceType(text: string): string {
  const t = (text || '').toLowerCase()
  if (t.includes('思维导图') || t.includes('mindmap')) return 'mindmap'
  if (t.includes('pdf')) return 'pdf'
  if (t.includes('doc') || t.includes('文档') || t.includes('word')) return 'doc'
  return 'ppt'
}

// ── resource_generate 桥接：POST 触发生成 → 轮询 task 进度 → WS 推 progress/done ──
async function bridgeResourceGenerate(
  sessionId: string,
  msgId: string,
  text: string,
  context: any
) {
  const intent = 'resource_generate'
  const base = config.services.resourceGen.replace(/\/$/, '')

  const resourceType = context?.resourceType || guessResourceType(text)

  let taskId: string
  try {
    const resp = await fetch(
      `${base}/api/v1/sessions/${sessionId}/resources/generate`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, resourceType }),
      }
    )
    const json = await resp.json()
    taskId = json?.data?.taskId
    if (!taskId) {
      throw new Error(`generate response missing taskId: ${JSON.stringify(json).slice(0, 200)}`)
    }
  } catch (e: any) {
    console.error('[WSRouter] resource_generate trigger failed:', e?.message || e)
    sendError(sessionId, msgId, intent, `资源生成触发失败: ${e?.message || e}`)
    return
  }
  console.log(`[WSRouter] resource_generate triggered: task=${taskId}`)
  sendProgress(sessionId, msgId, intent, taskId, 0, '已启动生成任务')

  // 轮询任务进度（每 2s 一次，最多 ~3 分钟）
  for (let i = 0; i < 90; i++) {
    await sleep(2000)
    try {
      const r = await fetch(`${base}/api/v1/resource-tasks/${taskId}`)
      const tj = await r.json()
      const task = tj?.data
      if (!task) continue
      sendProgress(
        sessionId,
        msgId,
        intent,
        taskId,
        task.progress ?? 0,
        task.progressDescription || ''
      )
      if (task.status === 'completed') {
        const res = task.result?.resources?.[0]
        sendText(
          sessionId,
          msgId,
          intent,
          `资源生成完成（${res?.type || resourceType}）：${res?.title || text}。可在「资源生成」查看或下载。`,
          'done'
        )
        return
      }
      if (task.status === 'failed') {
        sendError(sessionId, msgId, intent, `资源生成失败: ${task.error || '未知错误'}`)
        return
      }
    } catch (e: any) {
      console.warn('[WSRouter] poll task status error:', e?.message || e)
    }
  }
  sendError(sessionId, msgId, intent, '资源生成超时')
}

// ── path_query 桥接：GET learning-path 触发/确认路径生成，回引导帧 ──
async function bridgePathQuery(sessionId: string, msgId: string, text: string) {
  const intent = 'path_query'
  const base = config.services.pathPlanner.replace(/\/$/, '')
  try {
    const r = await fetch(`${base}/api/v1/sessions/${sessionId}/learning-path`)
    const j = await r.json()
    const nodes = j?.data?.nodes || []
    if (nodes.length) {
      const list = nodes
        .map((n: any, i: number) => `${i + 1}. ${n.title}`)
        .join('\n')
      sendText(
        sessionId,
        msgId,
        intent,
        `已为你生成定制学习路径，共 ${nodes.length} 个节点：\n${list}`
      )
      sendText(
        sessionId,
        msgId,
        intent,
        '可在左侧「我的学习路径」查看可视化时间线，含已完成/进行中/待学习节点。',
        'done'
      )
    } else {
      sendText(sessionId, msgId, intent, '路径生成中，请稍后在「我的学习路径」查看。', 'done')
    }
  } catch (e: any) {
    console.error('[WSRouter] path_query failed:', e?.message || e)
    sendText(sessionId, msgId, intent, '路径查询失败，请稍后重试。', 'done')
  }
}
