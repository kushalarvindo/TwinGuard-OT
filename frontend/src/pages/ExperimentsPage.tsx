import React, { useEffect, useState, useRef } from 'react';
import { api } from '../api';

type JobStatus = 'QUEUED' | 'RUNNING' | 'COMPLETED' | 'FAILED';

interface ExperimentType { id: string; name: string; description: string; }
interface Job {
  job_id: string;
  experiment_type: string;
  status: JobStatus;
  phase: string;
  elapsed_sec: number;
  result_path: string | null;
  error: string | null;
  progress_log: string[];
}

function statusBadge(s: JobStatus) {
  const map: Record<JobStatus, string> = { QUEUED: 'gray', RUNNING: 'blue', COMPLETED: 'green', FAILED: 'red' };
  return <span className={`badge ${map[s]}`}>{s}</span>;
}

export default function ExperimentsPage() {
  const [types, setTypes] = useState<ExperimentType[]>([]);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [params, setParams] = useState({ duration_sec: 25, warmup_sec: 6, cooldown_sec: 6 });
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const [selectedType, setSelectedType] = useState<string>('normal');
  const [starting, setStarting] = useState(false);
  const pollRef = useRef<number | null>(null);

  useEffect(() => {
    api.experiments.types().then(r => setTypes(r as ExperimentType[])).catch(() => {});
    api.experiments.jobs().then(r => setJobs(r as Job[])).catch(() => {});
  }, []);

  useEffect(() => {
    if (!activeJobId) return;
    const poll = () => {
      api.experiments.job(activeJobId).then(j => {
        const job = j as Job;
        setJobs(prev => {
          const idx = prev.findIndex(x => x.job_id === activeJobId);
          if (idx === -1) return [job, ...prev];
          const next = [...prev]; next[idx] = job; return next;
        });
        if (job.status === 'COMPLETED' || job.status === 'FAILED') {
          clearInterval(pollRef.current!);
          setActiveJobId(null);
        }
      }).catch(() => {});
    };
    pollRef.current = setInterval(poll, 1000) as unknown as number;
    return () => clearInterval(pollRef.current!);
  }, [activeJobId]);

  const startExperiment = async () => {
    setStarting(true);
    try {
      const r = await api.experiments.start(selectedType, params);
      setActiveJobId(r.job_id);
      setJobs(prev => [{ job_id: r.job_id, experiment_type: selectedType, status: 'QUEUED', phase: 'WAITING', elapsed_sec: 0, result_path: null, error: null, progress_log: [] }, ...prev]);
    } catch (e) {
      alert(`Failed: ${(e as Error).message}`);
    } finally {
      setStarting(false);
    }
  };

  const activeJob = activeJobId ? jobs.find(j => j.job_id === activeJobId) : null;

  return (
    <div>
      <div className="page-header">
        <div className="page-title">Experiments</div>
        <div className="page-sub">Run controlled attack experiments with baseline, warmup, attack, and cooldown phases</div>
      </div>

      <div className="grid-2-1">
        {/* Left: config */}
        <div>
          <div className="panel" style={{ marginBottom: 12 }}>
            <div className="panel-header"><span className="panel-title">New Experiment</span></div>
            <div className="panel-body">
              {/* Type selector */}
              <div style={{ marginBottom: 12 }}>
                <div className="field-label">Experiment Type</div>
                <select className="field-input" value={selectedType} onChange={e => setSelectedType(e.target.value)}>
                  {types.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
                </select>
              </div>

              <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 12, lineHeight: 1.5 }}>
                {types.find(t => t.id === selectedType)?.description}
              </div>

              {selectedType !== 'normal' && (
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 10, marginBottom: 14 }}>
                  <div>
                    <div className="field-label">Warmup (s)</div>
                    <input type="number" className="field-input" min={2} max={30} value={params.warmup_sec}
                      onChange={e => setParams(p => ({ ...p, warmup_sec: Number(e.target.value) }))} />
                  </div>
                  <div>
                    <div className="field-label">Attack (s)</div>
                    <input type="number" className="field-input" min={5} max={60} value={params.duration_sec}
                      onChange={e => setParams(p => ({ ...p, duration_sec: Number(e.target.value) }))} />
                  </div>
                  <div>
                    <div className="field-label">Cooldown (s)</div>
                    <input type="number" className="field-input" min={2} max={30} value={params.cooldown_sec}
                      onChange={e => setParams(p => ({ ...p, cooldown_sec: Number(e.target.value) }))} />
                  </div>
                </div>
              )}

              {selectedType === 'normal' && (
                <div style={{ marginBottom: 14 }}>
                  <div className="field-label">Duration (s)</div>
                  <input type="number" className="field-input" min={10} max={120} value={params.duration_sec}
                    onChange={e => setParams(p => ({ ...p, duration_sec: Number(e.target.value) }))} />
                </div>
              )}

              <button
                className="btn btn-primary"
                style={{ width: '100%', justifyContent: 'center' }}
                onClick={startExperiment}
                disabled={starting || Boolean(activeJobId)}
              >
                {starting ? 'Starting...' : activeJobId ? 'Running...' : '▶ Start Experiment'}
              </button>
            </div>
          </div>

          {/* Phase diagram */}
          {selectedType !== 'normal' && (
            <div className="panel">
              <div className="panel-header"><span className="panel-title">Experiment Phases</span></div>
              <div className="panel-body">
                <div style={{ display: 'flex', alignItems: 'center', gap: 0 }}>
                  {[
                    { label: 'BASELINE', color: 'var(--color-green)', sec: params.warmup_sec },
                    { label: 'ATTACK', color: 'var(--color-red)', sec: params.duration_sec },
                    { label: 'COOLDOWN', color: 'var(--color-blue)', sec: params.cooldown_sec },
                  ].map((phase, i) => (
                    <React.Fragment key={phase.label}>
                      <div style={{ textAlign: 'center', flex: phase.sec }}>
                        <div style={{ height: 6, background: phase.color, borderRadius: 3, marginBottom: 4, opacity: 0.7 }} />
                        <div style={{ fontSize: 9, color: 'var(--text-muted)', textTransform: 'uppercase' }}>{phase.label}</div>
                        <div style={{ fontSize: 9, color: 'var(--text-muted)' }}>{phase.sec}s</div>
                      </div>
                      {i < 2 && <div style={{ width: 4 }} />}
                    </React.Fragment>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Right: jobs */}
        <div>
          {activeJob && (
            <div className="panel" style={{ marginBottom: 12 }}>
              <div className="panel-header">
                <span className="panel-title">Running Experiment</span>
                {statusBadge(activeJob.status)}
              </div>
              <div className="panel-body">
                <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 8 }}>
                  {activeJob.experiment_type.toUpperCase().replace(/_/g, ' ')}
                </div>
                <div style={{ display: 'flex', gap: 16, marginBottom: 10, flexWrap: 'wrap' }}>
                  {[['Phase', activeJob.phase], ['Elapsed', `${activeJob.elapsed_sec.toFixed(1)}s`]].map(([k, v]) => (
                    <div key={k}>
                      <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>{k}</div>
                      <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', fontVariantNumeric: 'tabular-nums' }}>{v}</div>
                    </div>
                  ))}
                </div>
                <div style={{ maxHeight: 120, overflowY: 'auto' }}>
                  {activeJob.progress_log.map((line, i) => (
                    <div key={i} style={{ fontSize: 10, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', marginBottom: 2 }}>
                      {line}
                    </div>
                  ))}
                </div>
                {activeJob.error && (
                  <div style={{ marginTop: 8, fontSize: 11, color: 'var(--color-red)' }}>{activeJob.error}</div>
                )}
              </div>
            </div>
          )}

          <div className="panel">
            <div className="panel-header">
              <span className="panel-title">Experiment History</span>
              <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>{jobs.length} jobs</span>
            </div>
            {jobs.length === 0 ? (
              <div className="empty-state">No experiments run yet</div>
            ) : (
              <div className="panel-body no-pad">
                {jobs.map(j => (
                  <div key={j.job_id} style={{ padding: '8px 14px', borderBottom: '1px solid var(--border-light)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <div style={{ fontSize: 11.5, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 2 }}>
                        {j.experiment_type.replace(/_/g, ' ').toUpperCase()}
                      </div>
                      <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>
                        {j.elapsed_sec.toFixed(1)}s · Phase: {j.phase}
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
