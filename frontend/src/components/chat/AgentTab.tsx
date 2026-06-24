import React, { useState } from 'react'

interface AgentTabProps {
  active?: boolean
  /** dim=true 时灰显但仍可点击（软引导，不画锁、不写"待解锁"） */
  dim?: boolean
  onClick: () => void
  children: React.ReactNode
}

/**
 * 功能切换 Tab。
 * 选中态动画：放大 scale + 高亮边框/背景/投影；hover 轻微上浮。带弹性过渡。
 */
export const AgentTab: React.FC<AgentTabProps> = ({ active, dim, onClick, children }) => {
  const [hover, setHover] = useState(false)
  return (
    <span
      onClick={onClick}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={{
        display: 'inline-block',
        cursor: 'pointer',
        padding: active ? '8px 20px' : '6px 16px',
        borderRadius: '20px',
        fontSize: active ? '15px' : '14px',
        fontWeight: active ? 700 : 500,
        border: active ? '1.5px solid #722ed1' : '1px solid var(--glass-border)',
        background: active
          ? 'linear-gradient(135deg, rgba(24,144,255,0.28) 0%, rgba(114,46,209,0.22) 100%)'
          : hover
            ? 'var(--glass-bg)'
            : 'transparent',
        color: 'var(--text-color)',
        opacity: dim ? 0.55 : 1,
        transform: active ? 'scale(1.08)' : hover ? 'translateY(-2px)' : 'scale(1)',
        boxShadow: active
          ? '0 6px 18px rgba(114, 46, 209, 0.35)'
          : hover
            ? '0 4px 12px rgba(0, 0, 0, 0.12)'
            : 'none',
        transition:
          'transform .22s cubic-bezier(.34,1.56,.64,1), box-shadow .22s ease, background .22s ease, border-color .22s ease, padding .18s ease, font-size .18s ease, opacity .2s ease',
        userSelect: 'none',
      }}
    >
      {children}
    </span>
  )
}

export default AgentTab
