import React, { useEffect, useRef, useState } from 'react'
import { Card, Row, Col, List, Button, Typography, Space, message, Skeleton, Badge } from 'antd'
import { FireOutlined, BulbOutlined, EditOutlined } from '@ant-design/icons'
import * as echarts from 'echarts'
import { getEvaluationReport, submitEvaluation } from '../services/apiServices'
import { useAppState } from '../stores'
import type { EvaluationReport as ReportType } from '../types'

const { Title, Paragraph, Text } = Typography

export const EvaluationReport: React.FC = () => {
  const sessionId = useAppState((state) => state.sessionId)
  const currentTheme = useAppState((state) => state.theme)

  const [report, setReport] = useState<ReportType | null>(null)
  const [loading, setLoading] = useState(false)
  const [testing, setTesting] = useState(false)
  
  const chartContainerRef = useRef<HTMLDivElement>(null)
  const chartInstanceRef = useRef<echarts.ECharts | null>(null)

  const fetchReport = async () => {
    if (!sessionId) return
    setLoading(true)
    try {
      const response = await getEvaluationReport(sessionId)
      setReport(response)
    } catch (error: any) {
      console.error(error)
      message.error(error.message || '获取评估报告失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchReport()
  }, [sessionId])

  // Initialize and update ECharts Radar Chart
  useEffect(() => {
    if (loading || !report || !chartContainerRef.current) return

    // Initialize chart if not created
    if (!chartInstanceRef.current) {
      chartInstanceRef.current = echarts.init(chartContainerRef.current)
    }

    const myChart = chartInstanceRef.current
    const isDark = currentTheme === 'dark'

    // Set chart options
    const option = {
      backgroundColor: 'transparent',
      title: {
        text: '知识维度掌握度画像',
        left: 'center',
        textStyle: {
          color: isDark ? '#f8fafc' : '#0f172a',
          fontWeight: 600,
          fontSize: 16,
        },
      },
      tooltip: {
        trigger: 'item',
      },
      radar: {
        indicator: report.dimensions.map((dim) => ({
          name: dim.name,
          max: dim.maxScore,
        })),
        shape: 'polygon',
        splitNumber: 5,
        axisName: {
          color: isDark ? 'rgba(255, 255, 255, 0.65)' : '#475569',
          fontWeight: 500,
          fontSize: 12,
        },
        splitLine: {
          lineStyle: {
            color: isDark ? [
              'rgba(24, 144, 255, 0.06)',
              'rgba(24, 144, 255, 0.12)',
              'rgba(24, 144, 255, 0.2)',
              'rgba(24, 144, 255, 0.3)',
              'rgba(24, 144, 255, 0.4)',
            ].reverse() : [
              'rgba(24, 144, 255, 0.1)',
              'rgba(24, 144, 255, 0.2)',
              'rgba(24, 144, 255, 0.4)',
              'rgba(24, 144, 255, 0.6)',
              'rgba(24, 144, 255, 0.8)',
            ].reverse(),
          },
        },
        splitArea: {
          show: true,
          areaStyle: {
            color: isDark
              ? ['rgba(255, 255, 255, 0.01)', 'rgba(255, 255, 255, 0.03)']
              : ['rgba(248, 250, 252, 0.6)', 'rgba(241, 245, 249, 0.6)'],
          },
        },
        axisLine: {
          lineStyle: {
            color: isDark ? 'rgba(255, 255, 255, 0.15)' : 'rgba(0, 0, 0, 0.06)',
          },
        },
      },
      series: [
        {
          name: '当前能力模型',
          type: 'radar',
          data: [
            {
              value: report.dimensions.map((dim) => dim.score),
              name: '我的知识掌握度',
              symbol: 'circle',
              symbolSize: 6,
              lineStyle: {
                color: '#1890ff',
                width: 2,
              },
              itemStyle: {
                color: '#1890ff',
              },
              areaStyle: {
                color: new echarts.graphic.RadialGradient(0.5, 0.5, 1, [
                  {
                    color: isDark ? 'rgba(24, 144, 255, 0.45)' : 'rgba(24, 144, 255, 0.55)',
                    offset: 0,
                  },
                  {
                    color: isDark ? 'rgba(114, 46, 209, 0.1)' : 'rgba(114, 46, 209, 0.15)',
                    offset: 1,
                  },
                ]),
              },
            },
          ],
        },
      ],
    }

    myChart.setOption(option)

    // Handle container resize
    const handleResize = () => {
      myChart.resize()
    }
    window.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
    }
  }, [report, loading, currentTheme])

  // Dispose chart on unmount
  useEffect(() => {
    return () => {
      if (chartInstanceRef.current) {
        chartInstanceRef.current.dispose()
        chartInstanceRef.current = null
      }
    }
  }, [])

  // Mock quiz submission to simulate evaluation loop
  const handleQuizSubmit = async () => {
    if (!sessionId) return
    setTesting(true)
    try {
      // Send mock evaluation answers
      await submitEvaluation({
        sessionId,
        quizId: 'quiz_mock_789',
        answers: [
          { questionId: 'q1', answer: 'A', timeSpent: 20 },
          { questionId: 'q2', answer: 'C', timeSpent: 45 },
        ],
        behaviors: [
          { action: 'read_resource', resourceId: 'res_math_1', timestamp: new Date().toISOString() },
        ],
      })
      message.success('测评提交成功！正在基于最新的答题 and 学习行为重新评估学情画像...')
      // Wait a moment and fetch updated report
      setTimeout(() => {
        fetchReport()
      }, 1500)
    } catch (error: any) {
      console.error(error)
      message.error(error.message || '提交测评失败')
    } finally {
      setTesting(false)
    }
  }

  return (
    <div>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div>
          <Title level={3} style={{ margin: 0, fontWeight: 700 }}>
            学习评估报告
          </Title>
          <Paragraph style={{ color: 'var(--text-secondary)', margin: 0 }}>
            利用 AI 算法分析你的学习轨迹、测验成绩和行为日志，多维度量化并呈现你的知识掌握画像。
          </Paragraph>
        </div>
        
        <Button
          type="primary"
          icon={<EditOutlined />}
          loading={testing}
          onClick={handleQuizSubmit}
          style={{
            background: 'linear-gradient(135deg, #1890ff 0%, #722ed1 100%)',
            border: 'none',
            borderRadius: '6px',
            fontWeight: 600,
          }}
        >
          提交随堂测验 (重新测评)
        </Button>
      </div>

      {loading ? (
        <Card className="glass-panel" style={{ borderRadius: '12px' }}>
          <Skeleton active paragraph={{ rows: 8 }} />
        </Card>
      ) : report ? (
        <Row gutter={[24, 24]}>
          {/* Left Panel: ECharts Radar Chart */}
          <Col xs={24} md={12}>
            <Card
              className="glass-panel"
              style={{
                borderRadius: '12px',
                height: '100%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
              styles={{ body: { width: '100%', padding: '24px' } }}
            >
              <div
                ref={chartContainerRef}
                style={{
                  width: '100%',
                  height: '380px',
                  margin: '0 auto',
                }}
              />
            </Card>
          </Col>

          {/* Right Panel: Weaknesses and Suggestions */}
          <Col xs={24} md={12}>
            <Space direction="vertical" size="large" style={{ width: '100%' }}>
              {/* Weak Points Card */}
              <Card
                className="glass-panel"
                title={
                  <Space>
                    <FireOutlined style={{ color: '#ff4d4f' }} />
                    <Text style={{ fontWeight: 600, color: 'var(--text-color)' }}>薄弱知识点分析</Text>
                  </Space>
                }
                style={{
                  borderRadius: '12px',
                }}
              >
                <List
                  dataSource={report.weakPoints}
                  renderItem={(item) => (
                    <List.Item style={{ padding: '8px 0', border: 'none' }}>
                      <List.Item.Meta
                        avatar={<Badge status="error" />}
                        description={<Text style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>{item}</Text>}
                      />
                    </List.Item>
                  )}
                />
              </Card>

              {/* Suggestions Card */}
              <Card
                className="glass-panel"
                title={
                  <Space>
                    <BulbOutlined style={{ color: '#faad14' }} />
                    <Text style={{ fontWeight: 600, color: 'var(--text-color)' }}>个性化提升建议</Text>
                  </Space>
                }
                style={{
                  borderRadius: '12px',
                }}
              >
                <List
                  dataSource={report.suggestions}
                  renderItem={(item, index) => (
                    <List.Item style={{ padding: '8px 0', border: 'none' }}>
                      <List.Item.Meta
                        avatar={
                          <div
                            style={{
                              width: 20,
                              height: 20,
                              borderRadius: '50%',
                              backgroundColor: 'var(--blockquote-bg, rgba(114, 46, 209, 0.05))',
                              color: '#722ed1',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              fontSize: '11px',
                              fontWeight: 600,
                              border: '1px solid var(--glass-border)',
                            }}
                          >
                            {index + 1}
                          </div>
                        }
                        description={<Text style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>{item}</Text>}
                      />
                    </List.Item>
                  )}
                />
              </Card>
            </Space>
          </Col>
        </Row>
      ) : (
        <Card className="glass-panel" style={{ textAlign: 'center', padding: '40px 0' }}>
          <Text type="secondary">暂无评估报告，请提交随堂测验以激活评估算法。</Text>
        </Card>
      )}
    </div>
  )
}

export default EvaluationReport
