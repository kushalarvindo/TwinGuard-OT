import React from 'react';
import { useTelemetry } from '../hooks/useTelemetry';
import { ShieldAlert, ShieldOff } from 'lucide-react';

interface Props { telemetry: ReturnType<typeof useTelemetry>; }

function severityColor(s: string) {
  const m: Record<string, string> = { CRITICAL: 'red', HIGH: 'amber', MEDIUM: 'blue', INFO: 'gray' };
  return m[s] ?? 'gray';
}

function fmtTs(ts: number) {
  return new Date(ts * 1000).toLocaleString();
}

export default function DetectionPage({ telemetry }: Props) {
  const { latest, history } = telemetry;

  // Derive alert stream from history
  const alerts = history
    .filter(f => f.is_anomaly)
    .slice(-50)
    .reverse();

  const det = latest ? {
    is_anomaly: latest.is_anomaly,
    anomaly_score: latest.anomaly_score,
  } : null;

  return (
    <div>
      <div className="page-header">
        <div className="page-title">Detection & Alerts</div>
        <div className="page-sub">Real-time anomaly detection status and alert feed</div>
      </div>

      {/* Detection status */}
      <div className="grid-3" style={{ marginBottom: 14 }}>
        <div className="metric-card" style={{ borderColor: det?.is_anomaly ? 'rgba(239,68,68,0.3)' : 'rgba(34,197,94,0.2)' }}>
          <div className="metric-label">Detection Status</div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginTop: 4 }}>
            {det?.is_anomaly
              ? <ShieldOff size={28} color="var(--color-red)" />
              : <ShieldAlert size={28} color="var(--color-green)" />}
            <div>
              <div style={{ fontSize: 14, fontWeight: 700, color: det?.is_anomaly ? 'var(--color-red)' : 'var(--color-green)' }}>
                {det?.is_anomaly ? 'ANOMALY' : 'NORMAL'}
              </div>
              <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>Current status</div>
            </div>
          </div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Anomaly Score</div>
          <div className="metric-value" style={{ color: (det?.anomaly_score ?? 0) > 0.1 ? 'var(--color-red)' : 'var(--text-primary)' }}>
            {(det?.anomaly_score ?? 0).toFixed(4)}
          </div>
          <div className="metric-sub">ML Isolation Forest</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Alert Count (Session)</div>
          <div className="metric-value" style={{ color: alerts.length > 0 ? 'var(--color-amber)' : 'var(--text-primary)' }}>
            {alerts.length}
          </div>
          <div className="metric-sub">Anomaly frames detected</div>
        </div>
      </div>

      {/* Active spoofing indicator */}
      {latest?.sensor_spoofed && (
        <div className="attack-active-banner" style={{ marginBottom: 14 }}>
          ⚠ SENSOR SPOOFING DETECTED — True level: {latest.true_level.toFixed(1)}% vs Reported: {latest.sensor_level.toFixed(1)}%
          — Residual: {latest.residual.toFixed(1)}%
        </div>
      )}

      {/* Alert feed */}
      <div className="panel">
        <div className="panel-header">
          <span className="panel-title">Alert Feed</span>
          <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>{alerts.length} alerts</span>
        </div>
        <div style={{ maxHeight: 500, overflowY: 'auto' }}>
          {alerts.length === 0 ? (
            <div className="empty-state">
              <ShieldAlert size={24} style={{ marginBottom: 8, opacity: 0.3 }} />
              No anomalies detected in this session
            </div>
          ) : (
            alerts.map((f, i) => (
              <div key={i} className="alert-item">
                <div className="alert-bar CRITICAL" />
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <div className="alert-title">
                      {f.sensor_spoofed ? 'Sensor Spoofing — Physical Residual Violation'
                        : f.is_anomaly ? 'Anomaly Detected'
                        : 'Alert'}
                    </div>
                    <span className={`badge red`} style={{ flexShrink: 0 }}>ANOMALY</span>
                  </div>
                  <div className="alert-meta">
                    Score: {f.anomaly_score.toFixed(4)} · Residual: {f.residual.toFixed(1)}% · Level: {f.sensor_level.toFixed(1)}%
                    {f.active_attack && ` · Attack: ${f.active_attack}`}
                  </div>
                  <div className="alert-meta" style={{ marginTop: 2, fontFamily: 'var(--font-mono)', fontSize: 10 }}>
                    {fmtTs(f.timestamp)}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Detection rules */}
      <div className="panel" style={{ marginTop: 14 }}>
        <div className="panel-header"><span className="panel-title">Detection Rules</span></div>
        <div className="panel-body no-pad">
          {[
            { id: 'R001', name: 'Unexpected Pump Activation', category: 'PHYSICAL', desc: 'Pump ON while sensor level ≥ high threshold' },
            { id: 'R002', name: 'Process Residual Violation', category: 'HYBRID', desc: '|True − Sensor| > 10% — indicates spoofing' },
            { id: 'R003', name: 'Impossible Level Rate', category: 'PHYSICAL', desc: 'Rate of change exceeds max physical pump capacity' },
            { id: 'R004', name: 'High Request Rate Flood', category: 'CYBER', desc: 'Modbus request rate > 30 r/s — suspected DoS' },
            { id: 'R005', name: 'Abnormal Setpoint', category: 'HYBRID', desc: 'Setpoint outside safe operating envelope [15%, 90%]' },
            { id: 'R006', name: 'Frozen Sensor Detection', category: 'PHYSICAL', desc: 'Sensor static for > 15 scans while pump active' },
          ].map(r => (
            <div key={r.id} style={{ padding: '8px 14px', borderBottom: '1px solid var(--border-light)', display: 'flex', gap: 12, alignItems: 'flex-start' }}>
              <span className="mono" style={{ color: 'var(--text-muted)', fontSize: 11, minWidth: 40 }}>{r.id}</span>
              <div>
                <div style={{ fontSize: 11.5, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 2 }}>{r.name}</div>
                <div style={{ fontSize: 10.5, color: 'var(--text-muted)' }}>{r.desc}</div>
              </div>
              <span className={`badge ${r.category === 'PHYSICAL' ? 'blue' : r.category === 'CYBER' ? 'amber' : 'red'}`} style={{ marginLeft: 'auto', flexShrink: 0 }}>
                {r.category}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
