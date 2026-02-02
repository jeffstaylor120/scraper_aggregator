// frontend/src/pages/RunList.tsx
import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api, type NewsletterTemplate, type NewsletterRun } from '../api'

export function RunList() {
  const { templateId } = useParams<{ templateId: string }>()
  const id = templateId ? parseInt(templateId, 10) : NaN
  const [template, setTemplate] = useState<NewsletterTemplate | null>(null)
  const [runs, setRuns] = useState<NewsletterRun[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (Number.isNaN(id)) return
    Promise.all([api.getTemplate(id), api.listRuns(id)])
      .then(([t, r]) => {
        setTemplate(t)
        setRuns(r.runs)
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [id])

  if (Number.isNaN(id) || loading) return <p>Loading…</p>
  if (error || !template) return <p className="error">Error: {error || 'Template not found'}</p>

  return (
    <div className="page">
      <h1>{template.name}</h1>
      <p><Link to="/">← All templates</Link> · <Link to={`/templates/${id}/runs/new`}>+ New run</Link></p>
      <p className="muted">Runs (e.g. Q4 2025, Q1 2026): refine prompt or add resources per run, then generate.</p>
      <ul>
        {runs.map((r) => (
          <li key={r.id}>
            <Link to={`/runs/${r.id}`}>{r.label}</Link>
            {r.has_report ? ' ✓' : ' (no report yet)'}
          </li>
        ))}
      </ul>
      {runs.length === 0 && <p>No runs yet. Create one (e.g. label: Q4 2025) then generate.</p>}
    </div>
  )
}
