// frontend/src/pages/TemplateList.tsx
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, type NewsletterTemplate } from '../api'

export function TemplateList() {
  const [templates, setTemplates] = useState<NewsletterTemplate[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api.listTemplates()
      .then((r) => setTemplates(r.templates))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <p>Loading templates…</p>
  if (error) return <p className="error">Error: {error}</p>

  return (
    <div className="page">
      <h1>Newsletter templates</h1>
      <p><Link to="/templates/new">+ New template</Link></p>
      <ul>
        {templates.map((t) => (
          <li key={t.id}>
            <Link to={`/templates/${t.id}`}>{t.name}</Link>
            {t.use_web_search && <span> (web search)</span>}
          </li>
        ))}
      </ul>
      {templates.length === 0 && <p>No templates yet. Create one to get started.</p>}
    </div>
  )
}
