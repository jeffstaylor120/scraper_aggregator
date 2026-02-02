// frontend/src/pages/RunDetail.tsx
import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api, type NewsletterRunDetail } from '../api'

export function RunDetail() {
  const { runId } = useParams<{ runId: string }>()
  const id = runId ? parseInt(runId, 10) : NaN
  const [run, setRun] = useState<NewsletterRunDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [generating, setGenerating] = useState(false)
  const [genError, setGenError] = useState<string | null>(null)

  const load = () => {
    if (Number.isNaN(id)) return
    api.getRun(id)
      .then(setRun)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    load()
  }, [id])

  const handleGenerate = () => {
    if (Number.isNaN(id)) return
    setGenError(null)
    setGenerating(true)
    api.generateRun(id)
      .then((r) => {
        setRun((prev) => prev ? { ...prev, report_markdown: r.report_markdown } : null)
      })
      .catch((e) => setGenError(e.message))
      .finally(() => setGenerating(false))
  }

  if (Number.isNaN(id) || loading) return <p>Loading…</p>
  if (error || !run) return <p className="error">Error: {error || 'Run not found'}</p>

  return (
    <div className="page">
      <h1>{run.label}</h1>
      <p><Link to={`/templates/${run.template_id}`}>← {run.template_name}</Link></p>
      <p className="muted">Run of template; optional prompt override and extra URLs applied when generating.</p>
      <button onClick={handleGenerate} disabled={generating}>
        {generating ? 'Generating…' : 'Generate newsletter'}
      </button>
      {genError && <p className="error">{genError}</p>}
      {run.report_markdown && (
        <div className="report">
          <h2>Report</h2>
          <pre
            className="report-body"
            style={{ color: '#1a1a1a', background: '#f5f6f7' }}
          >
            {run.report_markdown}
          </pre>
        </div>
      )}
    </div>
  )
}
