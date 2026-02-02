// frontend/src/pages/RunForm.tsx
import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { api, type NewsletterRunIn } from '../api'

export function RunForm() {
  const { templateId } = useParams<{ templateId: string }>()
  const navigate = useNavigate()
  const id = templateId ? parseInt(templateId, 10) : NaN
  const [label, setLabel] = useState('')
  const [promptOverride, setPromptOverride] = useState('')
  const [extraUrls, setExtraUrls] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (Number.isNaN(id)) return
    setError(null)
    setSubmitting(true)
    const payload: NewsletterRunIn = {
      label: label.trim(),
      prompt_override: promptOverride.trim() || null,
      extra_source_urls: extraUrls.split('\n').map((u) => u.trim()).filter(Boolean),
    }
    api.createRun(id, payload)
      .then((r) => navigate(`/runs/${r.id}`))
      .catch((e) => setError(e.message))
      .finally(() => setSubmitting(false))
  }

  if (Number.isNaN(id)) return <p>Invalid template.</p>

  return (
    <div className="page">
      <h1>New run</h1>
      <p><Link to={`/templates/${id}`}>← Back to template</Link></p>
      <form onSubmit={handleSubmit}>
        <div>
          <label>Label (e.g. Q4 2025, Q1 2026)</label>
          <input value={label} onChange={(e) => setLabel(e.target.value)} required placeholder="Q4 2025" />
        </div>
        <div>
          <label>Prompt override (optional)</label>
          <textarea value={promptOverride} onChange={(e) => setPromptOverride(e.target.value)} rows={3} placeholder="Extra instructions for this run..." />
        </div>
        <div>
          <label>Extra source URLs to scrape for this run (one per line, optional)</label>
          <textarea value={extraUrls} onChange={(e) => setExtraUrls(e.target.value)} rows={3} placeholder="https://..." />
        </div>
        {error && <p className="error">{error}</p>}
        <button type="submit" disabled={submitting}>{submitting ? 'Creating…' : 'Create run'}</button>
      </form>
    </div>
  )
}
