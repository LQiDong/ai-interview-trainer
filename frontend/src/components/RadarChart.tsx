// SVG Radar (Spider) Chart for 4-dimension scores

interface RadarChartProps {
  data: { label: string; score: number; maxScore: number }[]
  size?: number
}

const COLORS = ['#2563eb', '#10b981', '#f59e0b', '#6366f1']

export default function RadarChart({ data, size = 240 }: RadarChartProps) {
  const cx = size / 2
  const cy = size / 2
  const radius = size * 0.35
  const levels = 4 // 0, 1, 2, 3 → 4 concentric levels

  const angleSlice = (2 * Math.PI) / data.length

  const getPoint = (i: number, value: number, maxVal: number) => {
    const angle = angleSlice * i - Math.PI / 2
    const r = (value / maxVal) * radius
    return { x: cx + r * Math.cos(angle), y: cy + r * Math.sin(angle) }
  }

  // Background grid
  const gridPolygons = []
  for (let level = 1; level <= levels; level++) {
    const r = (level / levels) * radius
    const points = data
      .map((_, i) => {
        const angle = angleSlice * i - Math.PI / 2
        return `${cx + r * Math.cos(angle)},${cy + r * Math.sin(angle)}`
      })
      .join(' ')
    gridPolygons.push(
      <polygon
        key={`grid-${level}`}
        points={points}
        fill="none"
        stroke="var(--color-border)"
        strokeWidth="1"
      />
    )
  }

  // Axis lines
  const axes = data.map((_, i) => {
    const end = getPoint(i, data[i].maxScore, data[i].maxScore)
    return (
      <line
        key={`axis-${i}`}
        x1={cx} y1={cy}
        x2={end.x} y2={end.y}
        stroke="var(--color-border)"
        strokeWidth="1"
      />
    )
  })

  // Score polygon
  const scorePoints = data
    .map((d, i) => {
      const p = getPoint(i, d.score, d.maxScore)
      return `${p.x},${p.y}`
    })
    .join(' ')

  // Labels
  const labels = data.map((d, i) => {
    const labelPoint = getPoint(i, d.maxScore * 1.25, d.maxScore)
    return (
      <text
        key={`label-${i}`}
        x={labelPoint.x}
        y={labelPoint.y}
        textAnchor="middle"
        dominantBaseline="middle"
        fill="var(--color-text)"
        fontSize="12"
        fontWeight="500"
      >
        {d.label}
      </text>
    )
  })

  // Score dots
  const dots = data.map((d, i) => {
    const p = getPoint(i, d.score, d.maxScore)
    return (
      <circle
        key={`dot-${i}`}
        cx={p.x} cy={p.y} r="4"
        fill={COLORS[i]}
      />
    )
  })

  return (
    <svg
      viewBox={`0 0 ${size} ${size}`}
      width={size}
      height={size}
      style={{ overflow: 'visible' }}
    >
      {gridPolygons}
      {axes}
      <polygon
        points={scorePoints}
        fill={`${COLORS[0]}20`}
        stroke={COLORS[0]}
        strokeWidth="2"
      />
      {dots}
      {labels}
    </svg>
  )
}
