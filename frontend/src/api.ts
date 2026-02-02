// frontend/src/api.ts — API client for FastAPI (proxied at /api in dev).

const BASE = '/api';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...options?.headers },
  });
  const text = await res.text();
  if (!res.ok) {
    throw new Error(text || `${res.status} ${res.statusText}`);
  }
  // If we got HTML (e.g. SPA index when proxy/API is down), don't parse as JSON
  const ct = res.headers.get('content-type') || '';
  if (!ct.includes('application/json') || text.trimStart().startsWith('<')) {
    throw new Error(
      'Backend returned HTML instead of JSON. Is the API running? Start it with: make dev (then open http://localhost:5173).'
    );
  }
  return JSON.parse(text) as T;
}

export const api = {
  health: () => request<{ ok: boolean }>('/health'),
  listTemplates: () => request<{ templates: NewsletterTemplate[] }>('/newsletter-templates'),
  createTemplate: (body: NewsletterTemplateIn) =>
    request<NewsletterTemplate>('/newsletter-templates', { method: 'POST', body: JSON.stringify(body) }),
  getTemplate: (id: number) => request<NewsletterTemplate>(`/newsletter-templates/${id}`),
  updateTemplate: (id: number, body: NewsletterTemplateIn) =>
    request<NewsletterTemplate>(`/newsletter-templates/${id}`, { method: 'PUT', body: JSON.stringify(body) }),
  deleteTemplate: (id: number) =>
    request<{ deleted: boolean; id: number }>(`/newsletter-templates/${id}`, { method: 'DELETE' }),
  listRuns: (templateId: number) =>
    request<{ runs: NewsletterRun[] }>(`/newsletter-templates/${templateId}/runs`),
  createRun: (templateId: number, body: NewsletterRunIn) =>
    request<NewsletterRun>(`/newsletter-templates/${templateId}/runs`, { method: 'POST', body: JSON.stringify(body) }),
  getRun: (runId: number) => request<NewsletterRunDetail>(`/newsletter-runs/${runId}`),
  updateRun: (runId: number, body: NewsletterRunUpdate) =>
    request<NewsletterRunDetail>(`/newsletter-runs/${runId}`, { method: 'PUT', body: JSON.stringify(body) }),
  deleteRun: (runId: number) =>
    request<{ deleted: boolean; id: number }>(`/newsletter-runs/${runId}`, { method: 'DELETE' }),
  generateRun: (runId: number) =>
    request<{ report_markdown: string }>(`/newsletter-runs/${runId}/generate`, { method: 'POST' }),
};

export interface NewsletterTemplate {
  id: number;
  name: string;
  system_prompt: string;
  source_urls: string[];
  example_content: string | null;
  use_web_search: boolean;
  created_at: string;
}

export interface NewsletterTemplateIn {
  name: string;
  system_prompt: string;
  source_urls?: string[];
  example_content?: string | null;
  use_web_search?: boolean;
}

export interface NewsletterRun {
  id: number;
  template_id: number;
  label: string;
  prompt_override: string | null;
  extra_source_urls: string[];
  feedback: string | null;
  has_report: boolean;
  created_at: string;
  updated_at: string;
}

export interface NewsletterRunIn {
  label: string;
  prompt_override?: string | null;
  extra_source_urls?: string[];
}

export interface NewsletterRunUpdate {
  label?: string;
  prompt_override?: string | null;
  extra_source_urls?: string[];
  feedback?: string | null;
}

export interface NewsletterRunDetail extends NewsletterRun {
  report_markdown: string | null;
  template_name: string;
  system_prompt: string;
  example_content: string | null;
  use_web_search: boolean;
}
