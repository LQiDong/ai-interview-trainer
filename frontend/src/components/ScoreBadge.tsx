interface ScoreBadgeProps {
  score: number
  maxScore: number
  label?: string
  size?: 'sm' | 'md' | 'lg'
}

const scoreColor = (ratio: number): string => {
  if (ratio >= 0.8) return 'var(--color-success)'
  if (ratio >= 0.5) return 'var(--color-warning)'
  return 'var(--color-danger)'
}

export default function ScoreBadge({ score, maxScore, label, size = 'md' }: ScoreBadgeProps) {
  const ratio = maxScore > 0 ? score / maxScore : 0
  const pct = Math.round(ratio * 100)
  const color = scoreColor(ratio)

  const sizeStyles: Record<string, { fontSize: string; padding: string }> = {
    sm: { fontSize: '0.75rem', padding: '2px 8px' },
    md: { fontSize: '0.875rem', padding: '4px 12px' },
    lg: { fontSize: '1.1rem', padding: '6px 16px' },
  }

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '4px',
        background: `${color}18`,
        color: color,
        fontWeight: 600,
        borderRadius: '6px',
        ...sizeStyles[size],
      }}
    >
      {label && <span style={{ fontWeight: 400, opacity: 0.8 }}>{label}</span>}
      <span>{score}/{maxScore}</span>
      <span style={{ fontSize: '0.7em', opacity: 0.7 }}>({pct}%)</span>
    </span>
  )
}
