import React, { useEffect, useState } from 'react'
import { Card, Select, Table, Space, Button, Typography, message, Tag } from 'antd'
import {
  DownloadOutlined,
  FilePdfOutlined,
  FilePptOutlined,
  FileWordOutlined,
  PlayCircleOutlined,
  DeploymentUnitOutlined,
  ReloadOutlined
} from '@ant-design/icons'
import { getResources } from '../services/apiServices'
import { useAppState } from '../stores'
import type { Resource } from '../types'

const { Text, Title, Paragraph } = Typography
const { Option } = Select

export const ResourceLibrary: React.FC = () => {
  const sessionId = useAppState((state) => state.sessionId)

  const [resources, setResources] = useState<Resource[]>([])
  const [loading, setLoading] = useState(false)
  const [filterType, setFilterType] = useState<string>('all')
  const [pagination, setPagination] = useState({ page: 1, pageSize: 10, total: 0 })

  const fetchResources = async (page = 1, type = filterType) => {
    if (!sessionId) return
    setLoading(true)
    try {
      const queryType = type === 'all' ? undefined : type
      const response = await getResources(sessionId, {
        page,
        pageSize: pagination.pageSize,
        type: queryType,
      })
      setResources(response.list || [])
      setPagination({
        page: response.pageInfo.page,
        pageSize: response.pageInfo.pageSize,
        total: response.pageInfo.total,
      })
    } catch (error: any) {
      console.error(error)
      message.error(error.message || '获取资源失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchResources(1, filterType)
  }, [sessionId, filterType])

  const handleTypeChange = (value: string) => {
    setFilterType(value)
    fetchResources(1, value)
  }

  const getIcon = (type: string) => {
    switch (type) {
      case 'pdf':
        return <FilePdfOutlined style={{ color: '#ff4d4f' }} />
      case 'ppt':
        return <FilePptOutlined style={{ color: '#d4380d' }} />
      case 'doc':
        return <FileWordOutlined style={{ color: '#1890ff' }} />
      case 'video':
        return <PlayCircleOutlined style={{ color: '#52c41a' }} />
      case 'mindmap':
      default:
        return <DeploymentUnitOutlined style={{ color: '#722ed1' }} />
    }
  }

  const getTag = (type: string) => {
    switch (type) {
      case 'pdf':
        return <Tag color="error">PDF 文档</Tag>
      case 'ppt':
        return <Tag color="warning">PPT 演示</Tag>
      case 'doc':
        return <Tag color="processing">Word 文档</Tag>
      case 'video':
        return <Tag color="success">微课视频</Tag>
      case 'mindmap':
      default:
        return <Tag color="purple">思维导图</Tag>
    }
  }

  const columns = [
    {
      title: '资源类型',
      dataIndex: 'type',
      key: 'type',
      width: 120,
      render: (text: string) => (
        <Space>
          {getIcon(text)}
          {getTag(text)}
        </Space>
      ),
    },
    {
      title: '资源标题',
      dataIndex: 'title',
      key: 'title',
      render: (text: string) => (
        <Text style={{ fontWeight: 600 }}>{text}</Text>
      ),
    },
    {
      title: '生成时间',
      dataIndex: 'createdAt',
      key: 'createdAt',
      width: 180,
      render: (text: string) => new Date(text).toLocaleString(),
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
      render: (_: any, record: Resource) => (
        <Button
          type="link"
          icon={<DownloadOutlined />}
          href={record.url}
          target="_blank"
          style={{ padding: 0 }}
        >
          查看/下载
        </Button>
      ),
    },
  ]

  return (
    <div>
      {/* Page Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div>
          <Title level={3} style={{ margin: 0, fontWeight: 700 }}>
            学习资源库
          </Title>
          <Paragraph style={{ color: 'var(--text-secondary)', margin: 0 }}>
            在此查看由画像和资源智能体为你定制生成的所有专属学习资源。
          </Paragraph>
        </div>
        <Button type="default" icon={<ReloadOutlined />} onClick={() => fetchResources(pagination.page)}>
          刷新列表
        </Button>
      </div>

      {/* Filter Toolbar */}
      <Card
        className="glass-panel"
        style={{ marginBottom: 20, borderRadius: '8px' }}
        styles={{ body: { padding: '16px' } }}
      >
        <Space size="large" align="center">
          <Text style={{ fontWeight: 500 }}>按类型筛选：</Text>
          <Select value={filterType} onChange={handleTypeChange} style={{ width: 160 }} size="middle">
            <Option value="all">📁 全部类型</Option>
            <Option value="pdf">📄 PDF 导读</Option>
            <Option value="ppt">📊 PPT 演示</Option>
            <Option value="doc">📝 Word 课件</Option>
            <Option value="mindmap">🧠 思维导图</Option>
            <Option value="video">🎬 微课视频</Option>
          </Select>
        </Space>
      </Card>

      {/* Resources Table */}
      <Table
        dataSource={resources}
        columns={columns}
        rowKey="resourceId"
        loading={loading}
        pagination={{
          current: pagination.page,
          pageSize: pagination.pageSize,
          total: pagination.total,
          onChange: (page) => fetchResources(page),
          showSizeChanger: false,
          showTotal: (total) => `共 ${total} 个资源`,
        }}
        style={{
          background: 'transparent',
          borderRadius: '8px',
        }}
      />
    </div>
  )
}

export default ResourceLibrary
