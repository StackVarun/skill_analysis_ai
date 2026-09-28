export default function ProgressBar({ score, label }) {
  return <div className="progress-wrap">
    {label && <div className="progress-label"><span>{label}</span><strong>{score ?? '—'}{score !== null && score !== undefined ? '%' : ''}</strong></div>}
    <div className="progress-track" role="progressbar" aria-label={label || 'Score'} aria-valuemin="0" aria-valuemax="100" aria-valuenow={score ?? 0}>
      <span style={{ width: `${Math.min(100, Math.max(0, Number(score) || 0))}%` }} />
    </div>
  </div>;
}
