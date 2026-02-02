// frontend/src/pages/NewsletterPage.tsx — Single compact page: templates with edit/expand, runs with CRUD + feedback.
import { useEffect, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import { api, type NewsletterTemplate, type NewsletterTemplateIn, type NewsletterRun, type NewsletterRunIn, type NewsletterRunUpdate, type NewsletterRunDetail } from '../api'
import { Modal } from '../components/Modal'

export function NewsletterPage() {
  const [templates, setTemplates] = useState<NewsletterTemplate[]>([])
  const [runsByTemplate, setRunsByTemplate] = useState<Record<number, NewsletterRun[]>>({})
  const [runDetails, setRunDetails] = useState<Record<number, NewsletterRunDetail>>({})
  const [expandedTemplateId, setExpandedTemplateId] = useState<number | null>(null)
  const [expandedRunId, setExpandedRunId] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Modals
  const [templateModal, setTemplateModal] = useState<{ open: boolean; edit: NewsletterTemplate | null }>({ open: false, edit: null })
  const [runModal, setRunModal] = useState<{ open: boolean; templateId: number; edit: NewsletterRun | null }>({ open: false, templateId: 0, edit: null })
  const [generatingRunId, setGeneratingRunId] = useState<number | null>(null)
  const [feedbackDirty, setFeedbackDirty] = useState<Record<number, string>>({})
  const [reportViewMode, setReportViewMode] = useState<'markdown' | 'raw'>('markdown')
  const [copiedRunId, setCopiedRunId] = useState<number | null>(null)

  const loadTemplates = () => {
    api.listTemplates()
      .then((r) => setTemplates(r.templates))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    loadTemplates()
  }, [])

  const loadRuns = (templateId: number) => {
    api.listRuns(templateId).then((r) =>
      setRunsByTemplate((prev) => ({ ...prev, [templateId]: r.runs }))
    )
  }

  const toggleTemplate = (id: number) => {
    setExpandedTemplateId((prev) => (prev === id ? null : id))
    if (!runsByTemplate[id]) loadRuns(id)
  }

  const loadRunDetail = (runId: number) => {
    api.getRun(runId).then((d) =>
      setRunDetails((prev) => ({ ...prev, [runId]: d }))
    )
  }

  const toggleRun = (runId: number) => {
    setExpandedRunId((prev) => (prev === runId ? null : runId))
    if (!runDetails[runId]) loadRunDetail(runId)
  }

  // Template CRUD
  const saveTemplate = (payload: NewsletterTemplateIn, id?: number) => {
    if (id) {
      api.updateTemplate(id, payload).then(() => { loadTemplates(); setTemplateModal({ open: false, edit: null }) })
    } else {
      api.createTemplate(payload).then(() => { loadTemplates(); setTemplateModal({ open: false, edit: null }) })
    }
  }

  const deleteTemplate = (id: number) => {
    if (!window.confirm('Delete this template and all its runs?')) return
    api.deleteTemplate(id).then(() => { loadTemplates(); setExpandedTemplateId((prev) => (prev === id ? null : prev)); setRunsByTemplate((prev) => { const next = { ...prev }; delete next[id]; return next }) })
  }

  // Run CRUD
  const saveRun = (templateId: number, payload: NewsletterRunIn, runId?: number) => {
    if (runId) {
      api.updateRun(runId, { label: payload.label, prompt_override: payload.prompt_override ?? null, extra_source_urls: payload.extra_source_urls ?? [] }).then(() => {
        loadRuns(templateId)
        if (runDetails[runId]) loadRunDetail(runId)
        setRunModal({ open: false, templateId: 0, edit: null })
      })
    } else {
      api.createRun(templateId, payload).then(() => { loadRuns(templateId); setRunModal({ open: false, templateId: 0, edit: null }) })
    }
  }

  const deleteRun = (templateId: number, runId: number) => {
    if (!window.confirm('Delete this run?')) return
    api.deleteRun(runId).then(() => { loadRuns(templateId); setExpandedRunId((prev) => (prev === runId ? null : prev)); setRunDetails((prev) => { const next = { ...prev }; delete next[runId]; return next }) })
  }

  const generateRun = (runId: number) => {
    setGeneratingRunId(runId)
    api.generateRun(runId)
      .then(() => {
        loadRunDetail(runId)
        const tid = Object.keys(runsByTemplate).map(Number).find((id) => runsByTemplate[id]?.some((rr) => rr.id === runId))
        if (tid != null) loadRuns(tid)
      })
      .catch(() => {})
      .finally(() => setGeneratingRunId(null))
  }

  const saveFeedback = (runId: number) => {
    const text = feedbackDirty[runId]
    if (text === undefined) return
    api.updateRun(runId, { feedback: text || null }).then(() => {
      setFeedbackDirty((prev) => { const next = { ...prev }; delete next[runId]; return next })
      loadRunDetail(runId)
    })
  }

  const copyReport = (runId: number) => {
    const text = runDetails[runId]?.report_markdown
    if (!text) return
    navigator.clipboard.writeText(text).then(() => {
      setCopiedRunId(runId)
      setTimeout(() => setCopiedRunId(null), 2000)
    })
  }

  if (loading) return <div className="page"><p>Loading…</p></div>
  if (error) return <div className="page"><p className="error">{error}</p></div>

  return (
    <div className="page">
      <h1>Newsletter templates</h1>
      <p>
        <button type="button" onClick={() => setTemplateModal({ open: true, edit: null })}>+ New template</button>
      </p>

      <ul style={{ listStyle: 'none', paddingLeft: 0 }}>
        {templates.map((t) => (
          <li key={t.id}>
            <div className="template-row">
              <span className="name">{t.name}</span>
              <button type="button" className="btn-sm" onClick={() => setTemplateModal({ open: true, edit: t })}>Edit</button>
              <button type="button" className="btn-sm" onClick={() => deleteTemplate(t.id)}>Delete</button>
              <button type="button" className="btn-sm" onClick={() => toggleTemplate(t.id)}>
                {expandedTemplateId === t.id ? '▲' : '▼'} Runs
              </button>
            </div>
            {expandedTemplateId === t.id && (
              <div className="run-list">
                <p>
                  <button type="button" className="btn-sm" onClick={() => setRunModal({ open: true, templateId: t.id, edit: null })}>+ New run</button>
                </p>
                {(runsByTemplate[t.id] || []).map((r) => (
                  <div key={r.id}>
                    <div className="run-row">
                      <span className="label">{r.label}</span>
                      <span>{r.has_report ? '✓' : '—'}</span>
                      <button type="button" className="btn-sm" onClick={() => setRunModal({ open: true, templateId: t.id, edit: r })}>Edit</button>
                      <button type="button" className="btn-sm" onClick={() => deleteRun(t.id, r.id)}>Delete</button>
                      <button type="button" className="btn-sm" disabled={generatingRunId === r.id} onClick={() => generateRun(r.id)}>
                        {generatingRunId === r.id ? '…' : 'Generate'}
                      </button>
                      <button type="button" className="btn-sm" onClick={() => toggleRun(r.id)}>
                        {expandedRunId === r.id ? '▲' : '▼'}
                      </button>
                    </div>
                    {expandedRunId === r.id && (
                      <div className="run-detail">
                        {!runDetails[r.id] ? (
                          <p className="muted">Loading…</p>
                        ) : (
                          <>
                            {runDetails[r.id].report_markdown && (
                              <div className="report">
                                <div className="report-toolbar">
                                  <span className="report-toolbar-label">View:</span>
                                  <button type="button" className={`btn-sm ${reportViewMode === 'markdown' ? 'active' : ''}`} onClick={() => setReportViewMode('markdown')}>Markdown</button>
                                  <button type="button" className={`btn-sm ${reportViewMode === 'raw' ? 'active' : ''}`} onClick={() => setReportViewMode('raw')}>Raw</button>
                                  <button type="button" className="btn-sm" onClick={() => copyReport(r.id)}>
                                    {copiedRunId === r.id ? 'Copied!' : 'Copy'}
                                  </button>
                                </div>
                                {reportViewMode === 'markdown' ? (
                                  <div className="report-body report-markdown">
                                    <ReactMarkdown>{runDetails[r.id].report_markdown}</ReactMarkdown>
                                  </div>
                                ) : (
                                  <pre className="report-body report-raw">{runDetails[r.id].report_markdown}</pre>
                                )}
                              </div>
                            )}
                            <div className="feedback-area">
                              <label>Feedback (emphasize X, include/exclude — used when you re-run Generate)</label>
                              <textarea
                                value={feedbackDirty[r.id] !== undefined ? feedbackDirty[r.id] : (runDetails[r.id].feedback ?? '')}
                                onChange={(e) => setFeedbackDirty((prev) => ({ ...prev, [r.id]: e.target.value }))}
                                placeholder="e.g. Emphasize fixed income; exclude China."
                              />
                              <button type="button" className="btn-sm" onClick={() => saveFeedback(r.id)}>Save feedback</button>
                            </div>
                          </>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </li>
        ))}
      </ul>

      {/* Template create/edit modal */}
      <Modal open={templateModal.open} onClose={() => setTemplateModal({ open: false, edit: null })} title={templateModal.edit ? 'Edit template' : 'New template'}>
        <TemplateForm
          initial={templateModal.edit}
          onSave={saveTemplate}
          onCancel={() => setTemplateModal({ open: false, edit: null })}
        />
      </Modal>

      {/* Run create/edit modal */}
      <Modal open={runModal.open} onClose={() => setRunModal({ open: false, templateId: 0, edit: null })} title={runModal.edit ? 'Edit run' : 'New run'}>
        <RunForm
          templateId={runModal.templateId}
          initial={runModal.edit}
          onSave={(p) => saveRun(runModal.templateId, p, runModal.edit?.id)}
          onCancel={() => setRunModal({ open: false, templateId: 0, edit: null })}
        />
      </Modal>
    </div>
  )
}

function TemplateForm({
  initial,
  onSave,
  onCancel,
}: {
  initial: NewsletterTemplate | null
  onSave: (p: NewsletterTemplateIn, id?: number) => void
  onCancel: () => void
}) {
  const [name, setName] = useState(initial?.name ?? '')
  const [systemPrompt, setSystemPrompt] = useState(initial?.system_prompt ?? '')
  const [sourceUrls, setSourceUrls] = useState((initial?.source_urls ?? []).join('\n'))
  const [exampleContent, setExampleContent] = useState(initial?.example_content ?? '')
  const [useWebSearch, setUseWebSearch] = useState(initial?.use_web_search ?? true)

  const payload = { name, system_prompt: systemPrompt, source_urls: sourceUrls.split('\n').map((u) => u.trim()).filter(Boolean), example_content: exampleContent || null, use_web_search: useWebSearch }
  return (
    <form onSubmit={(e) => { e.preventDefault(); onSave(payload, initial?.id) }}>
      <div><label>Name</label><input value={name} onChange={(e) => setName(e.target.value)} required /></div>
      <div><label>System prompt</label><textarea value={systemPrompt} onChange={(e) => setSystemPrompt(e.target.value)} rows={4} required /></div>
      <div><label>Source URLs (one per line)</label><textarea value={sourceUrls} onChange={(e) => setSourceUrls(e.target.value)} rows={2} /></div>
      <div><label>Example content</label><textarea value={exampleContent} onChange={(e) => setExampleContent(e.target.value)} rows={4} /></div>
      <div><label><input type="checkbox" checked={useWebSearch} onChange={(e) => setUseWebSearch(e.target.checked)} /> Use web search</label></div>
      <div style={{ marginTop: '1rem' }}>
        <button type="submit">Save</button>
        <button type="button" onClick={onCancel}>Cancel</button>
      </div>
    </form>
  )
}

function RunForm({
  templateId,
  initial,
  onSave,
  onCancel,
}: {
  templateId: number
  initial: NewsletterRun | null
  onSave: (p: NewsletterRunIn) => void
  onCancel: () => void
}) {
  const [label, setLabel] = useState(initial?.label ?? '')
  const [promptOverride, setPromptOverride] = useState(initial?.prompt_override ?? '')
  const [extraUrls, setExtraUrls] = useState((initial?.extra_source_urls ?? []).join('\n'))

  return (
    <form onSubmit={(e) => { e.preventDefault(); onSave({ label, prompt_override: promptOverride || null, extra_source_urls: extraUrls.split('\n').map((u) => u.trim()).filter(Boolean) }) }}>
      <div><label>Label (e.g. Q4 2025)</label><input value={label} onChange={(e) => setLabel(e.target.value)} required /></div>
      <div><label>Prompt override</label><textarea value={promptOverride} onChange={(e) => setPromptOverride(e.target.value)} rows={2} /></div>
      <div><label>Extra source URLs (one per line)</label><textarea value={extraUrls} onChange={(e) => setExtraUrls(e.target.value)} rows={2} /></div>
      <div style={{ marginTop: '1rem' }}>
        <button type="submit">Save</button>
        <button type="button" onClick={onCancel}>Cancel</button>
      </div>
    </form>
  )
}
