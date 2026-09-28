export function Loading({ label = 'Loading your workspace…' }) {
  return <div className="inline-loading"><span className="spinner" />{label}</div>;
}

export function ErrorNotice({ children, onRetry }) {
  if (!children) return null;
  return <div className="notice notice-error" role="alert"><span>{children}</span>{onRetry && <button className="text-button" onClick={onRetry}>Try again</button>}</div>;
}

export function EmptyState({ icon = '✦', title, children, action }) {
  return <div className="empty-state"><span className="empty-icon">{icon}</span><h3>{title}</h3><p>{children}</p>{action}</div>;
}

export function Notice({ tone = 'info', children }) {
  return <div className={`notice notice-${tone}`} role="status">{children}</div>;
}
