// frontend/src/pages/TemplateForm.tsx
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, type NewsletterTemplateIn } from '../api'

export function TemplateForm() {
  const navigate = useNavigate()
  const [name, setName] = useState('')
  const [systemPrompt, setSystemPrompt] = useState('')
  const [sourceUrls, setSourceUrls] = useState('')
  const [exampleContent, setExampleContent] = useState('')
  const [useWebSearch, setUseWebSearch] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setSubmitting(true)
    const payload: NewsletterTemplateIn = {
      name: name.trim(),
      system_prompt: systemPrompt.trim(),
      source_urls: sourceUrls.split('\n').map((u) => u.trim()).filter(Boolean),
      example_content: exampleContent.trim() || null,
      use_web_search: useWebSearch,
    }
    api.createTemplate(payload)
      .then((t) => navigate(`/templates/${t.id}`))
      .catch((e) => setError(e.message))
      .finally(() => setSubmitting(false))
  }

  return (
    <div className="page">
      <h1>New newsletter template</h1>
      <form onSubmit={handleSubmit}>
        <div>
          <label>Name</label>
          <input value={name} onChange={(e) => setName(e.target.value)} required />
        </div>
        <div>
          <label>System prompt (instructions for the newsletter)</label>
          <textarea value={systemPrompt} onChange={(e) => setSystemPrompt(e.target.value)} rows={6} required />
        </div>
        <div>
          <label>Source URLs to scrape (one per line, optional)</label>
          <textarea value={sourceUrls} onChange={(e) => setSourceUrls(e.target.value)} rows={3} placeholder="https://..." />
        </div>
        <div>
          <label>Example newsletter content (optional)</label>
          <textarea value={exampleContent} onChange={(e) => setExampleContent(e.target.value)} rows={8} placeholder="Paste example text for style/tone..." />
        </div>
        <div>
          <label>
            <input type="checkbox" checked={useWebSearch} onChange={(e) => setUseWebSearch(e.target.checked)} />
            Use OpenAI web search when generating
          </label>
        </div>
        {error && <p className="error">{error}</p>}
        <button type="submit" disabled={submitting}>{submitting ? 'Creating…' : 'Create template'}</button>
      </form>
    </div>
  )
}
