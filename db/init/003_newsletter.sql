-- Newsletter templates: system prompt, optional source URLs to scrape, optional example content, web search toggle.
CREATE TABLE IF NOT EXISTS newsletter_templates (
  id BIGSERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  system_prompt TEXT NOT NULL,
  source_urls JSONB NOT NULL DEFAULT '[]',
  example_content TEXT,
  use_web_search BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Runs per template: e.g. Q4 2025, Q1 2026; optional prompt override and extra URLs; generated report stored here.
CREATE TABLE IF NOT EXISTS newsletter_runs (
  id BIGSERIAL PRIMARY KEY,
  template_id BIGINT NOT NULL REFERENCES newsletter_templates(id) ON DELETE CASCADE,
  label TEXT NOT NULL,
  prompt_override TEXT,
  extra_source_urls JSONB NOT NULL DEFAULT '[]',
  report_markdown TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_newsletter_runs_template_id ON newsletter_runs (template_id);
