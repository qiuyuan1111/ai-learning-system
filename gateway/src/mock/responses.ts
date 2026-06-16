import { generateTraceId } from '../utils/idgen'
import { signToken } from '../utils/jwt'

// In-memory task progress simulator
const taskSimulators = new Map<string, { status: string; progress: number; startTime: number }>()

export function getMockSessionCreate(nickname: string, major: string, grade: string) {
  const sessionId = 'session_' + Math.random().toString(36).substr(2, 9)
  const token = signToken({ sessionId, nickname, major, grade })

  return {
    code: 200,
    message: 'SUCCESS',
    data: {
      sessionId,
      token,
      profile: {
        nickname,
        major,
        grade,
        stage: 'init'
      }
    },
    requestId: generateTraceId()
  }
}

export function getMockTaskStatus(taskId: string) {
  if (!taskSimulators.has(taskId)) {
    taskSimulators.set(taskId, {
      status: 'processing',
      progress: 0,
      startTime: Date.now()
    })
  }

  const task = taskSimulators.get(taskId)!

  if (task.status === 'processing') {
    task.progress += 25
    if (task.progress >= 100) {
      task.progress = 100
      task.status = 'completed'
    }
  }

  const responseData: any = {
    taskId,
    status: task.status,
    progress: task.progress
  }

  if (task.status === 'completed') {
    responseData.result = {
      resources: [
        {
          resourceId: 'res_' + Math.random().toString(36).substr(2, 9),
          type: 'pdf',
          title: '机器学习精髓导读手册.pdf',
          url: 'https://example.com/ml-guide.pdf',
          createdAt: new Date().toISOString()
        },
        {
          resourceId: 'res_' + Math.random().toString(36).substr(2, 9),
          type: 'mindmap',
          title: '机器学习核心知识点全景图.png',
          url: 'https://example.com/ml-mindmap.png',
          createdAt: new Date().toISOString()
        }
      ]
    }
  }

  return {
    code: 200,
    message: 'SUCCESS',
    data: responseData,
    requestId: generateTraceId()
  }
}

export function getMockLearningPath(sessionId: string) {
  return {
    code: 200,
    message: 'SUCCESS',
    data: {
      pathId: 'path_mock_456',
      updatedAt: new Date().toISOString(),
      nodes: [
        {
          nodeId: 'node_1',
          order: 1,
          title: '第一阶段：人工智能与机器学习数学基础',
          status: 'completed',
          resource: {
            resourceId: 'res_math_1',
            type: 'doc',
            url: 'https://example.com/math-basics.pdf'
          }
        },
        {
          nodeId: 'node_2',
          order: 2,
          title: '第二阶段：经典监督学习算法与回归分析',
          status: 'in_progress',
          resource: {
            resourceId: 'res_reg_1',
            type: 'ppt',
            url: 'https://example.com/regression-slide.ppt'
          }
        },
        {
          nodeId: 'node_3',
          order: 3,
          title: '第三阶段：深度学习入门与神经网络构建',
          status: 'pending',
          resource: {
            resourceId: 'res_dl_1',
            type: 'mindmap',
            url: 'https://example.com/dl-mindmap.png'
          }
        },
        {
          nodeId: 'node_4',
          order: 4,
          title: '第四阶段：大语言模型原理及微调实战项目',
          status: 'pending'
        }
      ]
    },
    requestId: generateTraceId()
  }
}

export function getMockEvaluationReport(sessionId: string) {
  return {
    code: 200,
    message: 'SUCCESS',
    data: {
      dimensions: [
        { name: '数学与统计基础', score: 85, maxScore: 100 },
        { name: '传统机器学习模型', score: 72, maxScore: 100 },
        { name: '神经网络与深度学习', score: 55, maxScore: 100 },
        { name: '工程实现与框架使用', score: 68, maxScore: 100 },
        { name: 'LLM 与 Prompt 工程', score: 40, maxScore: 100 }
      ],
      weakPoints: [
        '神经网络的反向传播原理理解较弱，难以进行底层优化',
        '在大语言模型（LLM）的 Prompt 设计和参数微调（Fine-Tuning）上缺乏实战经验',
        '高维矩阵操作及泛化过拟合调优有待提高'
      ],
      suggestions: [
        '建议优先阅读《深度学习》(花书) 的第6章和第7章，理解计算图与反向传播的数学公式',
        '利用我们提供的「神经网络构建」PPT 和思维导图资源进行系统性的概念复习',
        '结合本地运行环境，进行一次基于 Lora 或 QLora 的简易 LLM 微调项目实战',
        '在进行下一步学习时，配合辅导智能体针对反向传播数学公式进行多轮追问练习'
      ]
    },
    requestId: generateTraceId()
  }
}
