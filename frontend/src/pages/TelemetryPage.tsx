import React, { useState } from 'react';
import { useTelemetry } from '../hooks/useTelemetry';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';

interface Props { telemetry: ReturnType<typeof useTelemetry>; }

type Window = '30s' | '1m' | '5m' | '10m';
const WINDOW_SAMPLES: Record<Window, number> = { '30s': 150, '1m': 300, '5m': 600, '10m': 600 };

function fmtTime(ts: number) {
  return new Date(ts * 1000).toLocaleTimeString(undefined, { hour12: false });
}

export default function TelemetryPage({ telemetry }: Props) {
  const { latest, history, paused, setPaused } = telemetry;
  const [window_, setWindow] = useState<Window>('1m');

  const data = history.slice(-WINDOW_SAMPLES[window_]).map(f => ({
    t: fmtTime(f.timestamp),
    tank_level: f.sensor_level,
    true_level: f.true_level,
    inflow: f.inflow,
    outflow: f.outflow,
    residual: f.residual,
    request_rate: f.request_rate,
  }));

  if (!latest) {
    return <div className="loading-state"><div className="spinner" />Connecting...</div>;
  }

  const windowBtns: Window[] = ['30s', '1m', '5m', '10m'];

  return (
    <div>
      <div className="page-header" style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between' }}>
        <div>
          <div className="page-title">Live Telemetry</div>
          <div className="page-sub">Real-time sensor and process data streams</div>
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <span style={{ fontSize: 10, color: 'var(--text-muted)', marginRight: 4 }}>Window:</span>
          {windowBtns.map(w => (
            <button
              key={w}
              className={`btn btn-ghost`}
              style={{ padding: '4px 10px', fontSize: 11, ...(window_ === w ? { background: 'var(--color-blue-bg)', color: 'var(--color-blue)', borderColor: 'rgba(59,130,246,0.3)' } : {}) }}
              onClick={() => setWindow(w)}
            >{w}</button>
          ))}
          <button
            className={`btn ${paused ? 'btn-primary' : 'btn-ghost'}`}
            style={{ padding: '4px 12px', fontSize: 11 }}
            onClick={() => setPaused(!paused)}
          >
            {paused ? '▶ Resume' : '⏸ Pause'}
          </button>
        </div>
      </div>

      {/* Current readings row */}
      <div className="grid-4" style={{ marginBottom: 14 }}>
        {[
          { label: 'Tank Level', value: latest.sensor_level.toFixed(1), unit: '%', color: 'var(--color-blue)' },
          { label: 'Inflow', value: latest.inflow.toFixed(3), unit: '%/s', color: 'var(--color-green)' },
          { label: 'Outflow', value: latest.outflow.toFixed(3), unit: '%/s', color: 'var(--color-teal)' },
          { label: 'Residual', value: latest.residual.toFixed(2), unit: '%', color: latest.residual > 10 ? 'var(--color-red)' : 'var(--text-primary)' },
        ].map(m => (
          <div className="metric-card" key={m.label}>
            <div className="metric-label">{m.label}</div>
            <div className="metric-value" style={{ color: m.color }}>
              {m.value}<span className="metric-unit">{m.unit}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Charts */}
      {[
        { title: 'Tank Level', keys: [{ k: 'tank_level', name: 'Sensor', color: 'var(--chart-teal)', dash: false }, { k: 'true_level', name: 'True', color: 'var(--chart-blue)', dash: true }], refLines: [{ y: latest.high_threshold, color: 'var(--color-amber)' }, { y: latest.setpoint, color: 'var(--color-green)' }], unit: '%', domain: [0, 100] as [number, number] },
        { title: 'Inflow / Outflow', keys: [{ k: 'inflow', name: 'Inflow', color: 'var(--chart-green)', dash: false }, { k: 'outflow', name: 'Outflow', color: 'var(--chart-red)', dash: false }], refLines: [], unit: '%/s', domain: [0, 4] as [number, number] },
        { title: 'Physical Residual', keys: [{ k: 'residual', name: 'Residual', color: 'var(--chart-amber)', dash: false }], refLines: [{ y: 10, color: 'var(--color-red)' }], unit: '%', domain: [0, 60] as [number, number] },
        { title: 'Modbus Request Rate', keys: [{ k: 'request_rate', name: 'Rate', color: 'var(--chart-purple)', dash: false }], refLines: [{ y: 30, color: 'var(--color-amber)' }], unit: 'r/s', domain: [0, 200] as [number, number] },
      ].map(chart => (
        <div className="panel" key={chart.title} style={{ marginBottom: 12 }}>
          <div className="panel-header">
            <span className="panel-title">{chart.title}</span>
            <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>{chart.unit}</span>
          </div>
          <div className="panel-body" style={{ padding: '10px 4px 4px' }}>
            <ResponsiveContainer width="100%" height={120}>
              <LineChart data={data}>
                <XAxis dataKey="t" tick={{ fontSize: 9, fill: 'var(--text-muted)' }} tickLine={false} axisLine={false} interval="preserveStartEnd" />
                <YAxis domain={chart.domain} tick={{ fontSize: 9, fill: 'var(--text-muted)' }} tickLine={false} axisLine={false} width={28} unit={chart.unit} />
                <Tooltip contentStyle={{ background: 'var(--bg-overlay)', border: '1px solid var(--border)', borderRadius: 4, fontSize: 11 }} />
                {chart.refLines.map(rl => (
                  <ReferenceLine key={rl.y} y={rl.y} stroke={rl.color} strokeDasharray="3 3" strokeOpacity={0.5} />
                ))}
                {chart.keys.map(k => (
                  <Line key={k.k} type="monotone" dataKey={k.k} stroke={k.color} dot={false} strokeWidth={1.5} strokeDasharray={k.dash ? '4 2' : undefined} name={k.name} isAnimationActive={false} />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      ))}
    </div>
  );
}
