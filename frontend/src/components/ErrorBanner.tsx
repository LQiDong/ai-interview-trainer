interface ErrorBannerProps {
  message: string
  onRetry?: () => void
}

export default function ErrorBanner({ message, onRetry }: ErrorBannerProps) {
  return (
    <div className="error-banner">
      <span className="error-icon">⚠</span>
      <div style={{ flex: 1 }}>
        <div>{message}</div>
      </div>
      {onRetry && (
        <button className="btn btn-sm btn-outline" onClick={onRetry}>
          重试
        </button>
      )}
    </div>
  )
}
