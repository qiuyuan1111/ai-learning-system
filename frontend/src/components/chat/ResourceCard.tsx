import React from 'react'
import { Card, Button, Typography, Space } from 'antd'
import {
  FilePdfOutlined,
  FilePptOutlined,
  FileWordOutlined,
  PlayCircleOutlined,
  DeploymentUnitOutlined,
  DownloadOutlined
} from '@ant-design/icons'
import type { ResourceCard as ResourceCardType } from '../../types'

const { Text, Title, Paragraph } = Typography

interface ResourceCardProps {
  card: ResourceCardType
}

export const ResourceCard: React.FC<ResourceCardProps> = ({ card }) => {
  const getIcon = (type: string) => {
    switch (type) {
      case 'pdf':
        return <FilePdfOutlined style={{ fontSize: '32px', color: '#ff4d4f' }} />
      case 'ppt':
        return <FilePptOutlined style={{ fontSize: '32px', color: '#d4380d' }} />
      case 'doc':
        return <FileWordOutlined style={{ fontSize: '32px', color: '#1890ff' }} />
      case 'video':
        return <PlayCircleOutlined style={{ fontSize: '32px', color: '#52c41a' }} />
      case 'mindmap':
      default:
        return <DeploymentUnitOutlined style={{ fontSize: '32px', color: '#722ed1' }} />
    }
  };

  const getTypeName = (type: string) => {
    switch (type) {
      case 'pdf':
        return 'PDF 文档'
      case 'ppt':
        return 'PPT 演示'
      case 'doc':
        return 'Word 文档'
      case 'video':
        return '微课视频'
      case 'mindmap':
      default:
        return '思维导图'
    }
  };

  return (
    <Card
      hoverable
      style={{
        width: '100%',
        maxWidth: '360px',
        borderRadius: '12px',
        boxShadow: '0 4px 16px var(--glass-shadow)',
        border: '1px solid var(--glass-border)',
        background: 'var(--glass-bg)',
        backdropFilter: 'blur(8px)',
        overflow: 'hidden',
        marginTop: '8px',
      }}
      styles={{ body: { padding: '20px' } }}
    >
      <Space direction="vertical" size="middle" style={{ width: '100%' }}>
        <Space align="center" size="middle">
          <div
            style={{
              padding: '12px',
              borderRadius: '8px',
              background: 'var(--input-bg)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              border: '1px solid var(--glass-border)',
            }}
          >
            {getIcon(card.resourceType)}
          </div>
          <div>
            <Text type="secondary" style={{ fontSize: '12px', fontWeight: 500 }}>
              {getTypeName(card.resourceType)}
            </Text>
            <Title level={5} style={{ margin: 0, fontWeight: 600, fontSize: '14px', lineHeight: 1.3 }}>
              {card.title}
            </Title>
          </div>
        </Space>

        {card.description && (
          <Paragraph ellipsis={{ rows: 2 }} style={{ color: 'var(--text-secondary)', margin: 0, fontSize: '13px' }}>
            {card.description}
          </Paragraph>
        )}

        <Button
          type="primary"
          ghost
          icon={<DownloadOutlined />}
          href={card.url}
          target="_blank"
          style={{
            width: '100%',
            borderRadius: '6px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontWeight: 500,
          }}
        >
          查看 / 下载资源
        </Button>
      </Space>
    </Card>
  )
}
export default ResourceCard
