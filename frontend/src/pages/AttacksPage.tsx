import React, { useEffect, useState, useRef } from 'react';
import { api } from '../api';

type AttackStatus = 'QUEUED' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'STOPPED';

interface AttackCatalogueItem {
  id: string;
  name: string;
  description: string;
  category: string;
  severity: string;
  target: string;
  params: Record<string, { type: string; default: number; min: number; max: number; description: string }>;
  expected_effect: string;
}

interface Job {
  job_id: string;
  attack_type: string;
  status: AttackStatus;
  elapsed_sec: number;
  duration_sec: number;
  progress: number;
  events_injected: number;
  metrics: Record<string, unknown>;
  error: string | null;
}

function ProgressBar({ value, status }: { value: number; status: AttackStatus }) {
  const color = status === 'RUNNING' ? 'blue' : status === 'COMPLETED' ? 'green' : status === 'FAILED' ? 'red' : 'amber';
  return (
    <div className="progress-track">
      <div className={`progress-fill ${color}`} style={{ width: `${Math.round(value * 100)}%` }} />
    </div>
  );
}

function statusBadge(s: AttackStatus) {
  const map: Record<AttackStatus, string> = { QUEUED: 'gray', RUNNING: 'blue', COMPLETED: 'green', FAILED: 'red', STOPPED: 'amber' };
  return <span className={`badge ${map[s]}`}>{s}</span>;
}

export default function AttacksPage() {
  const [catalogue, setCatalogue] = useState<AttackCatalogueItem[]>([]);
  const [selected, setSelected] = useState<AttackCatalogueItem | null>(null);
  const [params, setParams] = useState<Record<string, number>>({});
  const [jobs, setJobs] = useState<Job[]>([]);
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const [starting, setStarting] = useState(false);
  const pollRef = useRef<number | null>(null);

  useEffect(() => {
    api.attacks.catalogue().then(r => setCatalogue(r as AttackCatalogueItem[])).catch(() => {});
    api.attacks.jobs().then(r => setJobs(r as Job[])).catch(() => {});
  }, []);

  // Poll active job
  useEffect(() => {
    if (!activeJobId) return;
    const poll = () => {
      api.attacks.job(activeJobId).then(j => {
        const job = j as Job;
        setJobs(prev => {
          const idx = prev.findIndex(x => x.job_id === activeJobId);
          if (idx === -1) return [job, ...prev];
          const next = [...prev];
          next[idx] = job;
          return next;
        });
        if (job.status === 'COMPLETED' || job.status === 'FAILED' || job.status === 'STOPPED') {
          clearInterval(pollRef.current!);
          setActiveJobId(null);
        }
      }).catch(() => {});
    };
    pollRef.current = setInterval(poll, 500) as unknown as number;
    return () => clearInterval(pollRef.current!);
  }, [activeJobId]);

  const selectAttack = (a: AttackCatalogueItem) => {
    setSelected(a);
    const defaults: Record<string, number> = {};
    for (const [k, v] of Object.entries(a.params)) {
      defaults[k] = v.default;
    }
    setParams(defaults);
  };

  const startAttack = async () => {
    if (!selected) return;
    setStarting(true);
    try {
      const r = await api.attacks.start(selected.id, params);
      setActiveJobId(r.job_id);
      setJobs(prev => [{ job_id: r.job_id, attack_type: selected.id, status: 'QUEUED', elapsed_sec: 0, duration_sec: params.duration_sec ?? 10, progress: 0, events_injected: 0, metrics: {}, error: null }, ...prev]);
    } catch (e) {
      alert(`Failed to start attack: ${(e as Error).message}`);
    } finally {
      setStarting(false);
    }
  };

  const stopAttack = async (job_id: string) => {
    await api.attacks.stop(job_id).catch(() => {});
  };

  const activeJob = activeJobId ? jobs.find(j => j.job_id === activeJobId) : null;
  const severityColor: Record<string, string> = { CRITICAL: 'red', HIGH: 'amber', MEDIUM: 'blue', LOW: 'gray' };

  return (
    <div>
      <div className="page-header">
        <div className="page-title">Attack Simulator</div>
        <div className="page-sub">
          Controlled ICS cyberattack scenarios — strictly confined to local simulation (127.0.0.1:5020)
        </div>
      </div>

      {/* Safety notice */}
      <div style={{ background: 'rgba(245,158,11,0.07)', border: '1px solid rgba(245,158,11,0.2)', borderRadius: 5, padding: '8px 14px', marginBottom: 14, fontSize: 11, color: 'var(--color-amber)' }}>
        ⚠ LOCAL SIMULATION ENVIRONMENT — All attacks target 127.0.0.1:5020 only. No external systems are affected.
      </div>

      <div className="grid-2-1">
        {/* Left: catalogue + config */}
        <div>
          {/* Attack catalogue */}
          <div className="panel" style={{ marginBottom: 12 }}>
            <div className="panel-header"><span className="panel-title">Attack Catalogue</span></div>
            <div className="panel-body no-pad">
              {catalogue.map(a => (
                <div
                  key={a.id}
                  onClick={() => selectAttack(a)}
                  style={{
                    padding: '10px 14px',
                    borderBottom: '1px solid var(--border-light)',
                    cursor: 'pointer',
                    background: selected?.id === a.id ? 'var(--bg-raised)' : 'transparent',
                    transition: 'background 0.1s',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 3 }}>
                    <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-primary)' }}>{a.name}</span>
                    <span className={`badge ${severityColor[a.severity] ?? 'gray'}`}>{a.severity}</span>
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{a.description}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Configuration + launch */}
          {selected && (
            <div className="panel">
              <div className="panel-header">
                <span className="panel-title">Configure: {selected.name}</span>
                <span className="badge gray">{selected.target}</span>
              </div>
              <div className="panel-body">
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 12, lineHeight: 1.5 }}>
                  <strong style={{ color: 'var(--text-secondary)' }}>Expected Effect:</strong> {selected.expected_effect}
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginBottom: 14 }}>
                  {Object.entries(selected.params).map(([key, meta]) => (
                    <div key={key}>
                      <div className="field-label">{meta.description}</div>
                      <input
                        type="number"
                        className="field-input"
                        min={meta.min}
                        max={meta.max}
                        step={meta.type === 'int' ? 1 : 0.1}
                        value={params[key] ?? meta.default}
                        onChange={e => setParams(p => ({ ...p, [key]: Number(e.target.value) }))}
                      />
                    </div>
                  ))}
                </div>
                <button
                  className="btn btn-danger"
                  style={{ width: '100%', justifyContent: 'center' }}
                  onClick={startAttack}
                  disabled={starting || Boolean(activeJobId)}
                >
                  {starting ? 'Starting...' : activeJobId ? 'Attack Running' : `⚡ Execute ${selected.name}`}
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Right: active job + history */}
        <div>
          {/* Active job monitor */}
          {activeJob && (
            <div className="panel" style={{ marginBottom: 12, borderColor: 'rgba(239,68,68,0.2)' }}>
              <div className="panel-header">
                <span className="panel-title">Active Attack</span>
                {statusBadge(activeJob.status)}
              </div>
              <div className="panel-body">
                <div style={{ marginBottom: 10 }}>
                  <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 6 }}>
                    {activeJob.attack_type.replace(/_/g, ' ').toUpperCase()}
                  </div>
                  <ProgressBar value={activeJob.progress} status={activeJob.status} />
                </div>
                <table style={{ width: '100%', fontSize: 11.5 }}>
                  <tbody>
                    {[
                      ['Elapsed', `${activeJob.elapsed_sec.toFixed(1)}s`],
                      ['Duration', `${activeJob.duration_sec}s`],
                      ['Events', activeJob.events_injected.toString()],
                      ['Target', '127.0.0.1:5020'],
                    ].map(([k, v]) => (
                      <tr key={k}>
                        <td style={{ color: 'var(--text-muted)', padding: '3px 0' }}>{k}</td>
                        <td style={{ color: 'var(--text-primary)', textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>{v}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {activeJob.status === 'RUNNING' && (
                  <button
                    className="btn btn-ghost"
                    style={{ width: '100%', marginTop: 10, justifyContent: 'center', fontSize: 11 }}
                    onClick={() => stopAttack(activeJob.job_id)}
                  >
                    ■ Stop Attack
                  </button>
                )}
                {activeJob.error && (
                  <div style={{ marginTop: 8, fontSize: 11, color: 'var(--color-red)' }}>{activeJob.error}</div>
                )}
              </div>
            </div>
          )}

          {/* Job history */}
          <div className="panel">
            <div className="panel-header">
              <span className="panel-title">Attack History</span>
              <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>{jobs.length} jobs</span>
            </div>
            {jobs.length === 0 ? (
              <div className="empty-state">No attacks executed yet</div>
            ) : (
              <div className="panel-body no-pad">
                {jobs.map(j => (
                  <div key={j.job_id} style={{ padding: '8px 14px', borderBottom: '1px solid var(--border-light)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <div style={{ fontSize: 11.5, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 2 }}>
                        {j.attack_type.replace(/_/g, ' ').toUpperCase()}
                      </div>
                      <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>
                        {j.elapsed_sec.toFixed(1)}s · {j.events_injected} events
                      </div>
                    </div>
                    {statusBadge(j.status)}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
