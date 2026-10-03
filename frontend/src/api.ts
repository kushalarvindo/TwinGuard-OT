// API client — all calls proxy to the FastAPI backend via Vite dev server proxy

const BASE = '/api';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    let msg = `HTTP ${res.status}`;
    try { const body = await res.json(); msg = body.detail || msg; } catch {}
    throw new Error(msg);
  }
  return res.json() as Promise<T>;
}

// --- System ---
export const api = {
  system: {
    status: () => request<Record<string, string>>('/system/status'),
  },

  twin: {
    state: () => request<Record<string, unknown>>('/twin/state'),
    plcStatus: () => request<Record<string, unknown>>('/twin/plc/status'),
  },

  telemetry: {
    recent: (limit = 300) => request<Record<string, unknown>[]>(`/telemetry?limit=${limit}`),
    latest: () => request<Record<string, unknown>>('/telemetry/latest'),
  },

  modbus: {
    status: () => request<Record<string, unknown>>('/modbus/status'),
    registers: () => request<Record<string, unknown>[]>('/modbus/registers'),
    events: (limit = 100) => request<Record<string, unknown>[]>(`/modbus/events?limit=${limit}`),
  },

  attacks: {
    catalogue: () => request<Record<string, unknown>[]>('/attacks'),
    start: (attack_type: string, params: Record<string, unknown>) =>
      request<{ job_id: string; status: string }>('/attacks/start', {
        method: 'POST',
        body: JSON.stringify({ attack_type, params }),
      }),
    jobs: () => request<Record<string, unknown>[]>('/attacks/jobs'),
    job: (job_id: string) => request<Record<string, unknown>>(`/attacks/${job_id}`),
    stop: (job_id: string) =>
      request<{ job_id: string; status: string }>(`/attacks/${job_id}/stop`, { method: 'POST' }),
  },

  detection: {
    status: () => request<Record<string, unknown>>('/detection/status'),
    alerts: (limit = 50) => request<Record<string, unknown>[]>(`/detection/alerts?limit=${limit}`),
  },

  experiments: {
    types: () => request<Record<string, unknown>[]>('/experiments/types'),
    list: () => request<Record<string, unknown>[]>('/experiments'),
    start: (experiment_type: string, params: Record<string, unknown>) =>
      request<{ job_id: string; status: string }>('/experiments/start', {
        method: 'POST',
        body: JSON.stringify({ experiment_type, params }),
      }),
    jobs: () => request<Record<string, unknown>[]>('/experiments/jobs'),
    job: (job_id: string) => request<Record<string, unknown>>(`/experiments/jobs/${job_id}`),
  },

  analytics: {
    anomaly: (experiment_id?: string) =>
      request<Record<string, unknown>>(`/analytics/anomaly${experiment_id ? `?experiment_id=${experiment_id}` : ''}`),
    evaluation: () => request<Record<string, unknown>[]>('/analytics/evaluation'),
    recompute: () =>
      request<{ status: string; results?: unknown; detail?: string }>('/analytics/recompute', {
        method: 'POST',
      }),
  },

  datasets: {
    list: () => request<Record<string, unknown>[]>('/datasets'),
    get: (id: string) => request<Record<string, unknown>>(`/datasets/${id}`),
    downloadUrl: (id: string) => `${BASE}/datasets/${id}/download`,
  },
};
