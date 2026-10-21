import React from 'react';
import { useTelemetry } from '../hooks/useTelemetry';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';
import ThreeTankRig from '../components/ThreeTankRig';

interface Props { telemetry: ReturnType<typeof useTelemetry>; }

function fmtTime(ts: number) {
  return new Date(ts * 1000).toLocaleTimeString(undefined, { hour12: false, second: '2-digit' });
}

export default function DigitalTwinPage({ telemetry }: Props) {
  const { latest, history } = telemetry;

  if (!latest) {
    return <div className="loading-state"><div className="spinner" />Connecting...</div>;
  }

  const chartData = history.slice(-200).map(f => ({
    t: fmtTime(f.timestamp),
    true_level: f.true_level,
    sensor_level: f.sensor_level,
    residual: f.residual,
  }));

  const diff = Math.abs(latest.true_level - latest.sensor_level);
  const isSpoofed = latest.sensor_spoofed;

  return (
    <div>
      <div className="page-header">
        <div className="page-title">Digital Twin</div>
        <div className="page-sub">True physical state vs. reported sensor state — ground-truth comparison</div>
      </div>

      {isSpoofed && (
        <div className="attack-active-banner">
          ⚠ SENSOR SPOOFING ACTIVE — Reported sensor reading is falsified. True physical state diverges from PLC inputs.
        </div>
      )}

      {/* True vs Sensor comparison */}
      <div className="grid-3" style={{ marginBottom: 14 }}>
        <div className="metric-card" style={{ borderColor: 'rgba(59,130,246,0.2)' }}>
          <div className="metric-label">True Level</div>
          <div className="metric-value" style={{ color: 'var(--color-blue)' }}>
            {latest.true_level.toFixed(2)}
            <span className="metric-unit">%</span>
          </div>
          <div className="metric-sub">Physical process — ground truth</div>
        </div>
        <div className="metric-card" style={{ borderColor: isSpoofed ? 'rgba(239,68,68,0.3)' : 'rgba(20,184,166,0.2)' }}>
          <div className="metric-label">Reported Level</div>
          <div className="metric-value" style={{ color: isSpoofed ? 'var(--color-red)' : 'var(--color-teal)' }}>
            {latest.sensor_level.toFixed(2)}
            <span className="metric-unit">%</span>
          </div>
          <div className="metric-sub">{isSpoofed ? '⚠ Spoofed value — PLC deceived' : 'Sensor with noise'}</div>
        </div>
        <div className="metric-card" style={{ borderColor: diff > 10 ? 'rgba(239,68,68,0.3)' : 'rgba(255,255,255,0.07)' }}>
          <div className="metric-label">Discrepancy</div>
          <div className="metric-value" style={{ color: diff > 10 ? 'var(--color-red)' : diff > 5 ? 'var(--color-amber)' : 'var(--color-green)' }}>
            {diff.toFixed(2)}
            <span className="metric-unit">%</span>
          </div>
          <div className="metric-sub">{diff > 10 ? 'ANOMALY — Residual threshold exceeded' : diff > 5 ? 'Elevated residual' : 'Within tolerance'}</div>
        </div>
      </div>

      {/* 3D Cyber-Physical Shadow Rig */}
      <div className="panel" style={{ marginBottom: 14 }}>
        <div className="panel-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span className="panel-title">3D Cyber-Physical Digital Twin Rig</span>
            <span className="badge blue">PBR REAL-TIME</span>
          </div>
          <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
            Physical Ground Truth (Left) vs. Sensor Reported (Right)
          </span>
        </div>
        <div className="panel-body no-pad">
          <ThreeTankRig frame={latest} height={320} />
        </div>
      </div>

      {/* Twin chart */}
      <div className="panel" style={{ marginBottom: 14 }}>
        <div className="panel-header">
          <span className="panel-title">True vs Sensor Level</span>
          <div style={{ display: 'flex', gap: 12 }}>
            <span style={{ fontSize: 10, color: 'var(--color-blue)', display: 'flex', alignItems: 'center', gap: 4 }}>
              <span style={{ width: 12, height: 2, background: 'var(--color-blue)', display: 'inline-block' }} /> True
            </span>
            <span style={{ fontSize: 10, color: 'var(--color-teal)', display: 'flex', alignItems: 'center', gap: 4 }}>
              <span style={{ width: 12, height: 2, display: 'inline-block', borderTop: '2px dashed var(--color-teal)', background: 'transparent' }} /> Sensor
            </span>
          </div>
        </div>
        <div className="panel-body" style={{ padding: '12px 4px 4px' }}>
          <ResponsiveContainer width="100%" height={180}>
            <LineChart data={chartData}>
              <XAxis dataKey="t" tick={{ fontSize: 9, fill: 'var(--text-muted)' }} tickLine={false} axisLine={false} interval="preserveStartEnd" />
              <YAxis domain={[0, 100]} tick={{ fontSize: 9, fill: 'var(--text-muted)' }} tickLine={false} axisLine={false} width={28} unit="%" />
              <Tooltip
                contentStyle={{ background: 'var(--bg-overlay)', border: '1px solid var(--border)', borderRadius: 4, fontSize: 11 }}
                formatter={(v: number, name: string) => [v.toFixed(2) + '%', name]}
              />
              <ReferenceLine y={latest.high_threshold} stroke="var(--color-amber)" strokeDasharray="3 3" strokeOpacity={0.4} label={{ value: 'High', fontSize: 9, fill: 'var(--color-amber)' }} />
              <ReferenceLine y={latest.setpoint} stroke="var(--color-green)" strokeDasharray="3 3" strokeOpacity={0.4} label={{ value: 'SP', fontSize: 9, fill: 'var(--color-green)' }} />
              <ReferenceLine y={latest.low_threshold} stroke="var(--color-blue)" strokeDasharray="3 3" strokeOpacity={0.3} label={{ value: 'Low', fontSize: 9, fill: 'var(--color-blue)' }} />
              <Line type="monotone" dataKey="true_level" stroke="var(--chart-blue)" dot={false} strokeWidth={2} name="True Level" isAnimationActive={false} />
              <Line type="monotone" dataKey="sensor_level" stroke="var(--chart-teal)" dot={false} strokeWidth={1.5} strokeDasharray="4 2" name="Sensor Level" isAnimationActive={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Residual chart */}
      <div className="panel" style={{ marginBottom: 14 }}>
        <div className="panel-header">
          <span className="panel-title">Physical Residual |True − Sensor|</span>
          <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>Threshold: 10%</span>
        </div>
        <div className="panel-body" style={{ padding: '12px 4px 4px' }}>
          <ResponsiveContainer width="100%" height={120}>
            <LineChart data={chartData}>
              <XAxis dataKey="t" tick={{ fontSize: 9, fill: 'var(--text-muted)' }} tickLine={false} axisLine={false} interval="preserveStartEnd" />
              <YAxis tick={{ fontSize: 9, fill: 'var(--text-muted)' }} tickLine={false} axisLine={false} width={28} unit="%" />
              <Tooltip contentStyle={{ background: 'var(--bg-overlay)', border: '1px solid var(--border)', borderRadius: 4, fontSize: 11 }} />
              <ReferenceLine y={10} stroke="var(--color-red)" strokeDasharray="3 3" strokeOpacity={0.5} label={{ value: 'Threshold', fontSize: 9, fill: 'var(--color-red)' }} />
              <Line type="monotone" dataKey="residual" stroke="var(--chart-amber)" dot={false} strokeWidth={1.5} name="Residual" isAnimationActive={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Component status */}
      <div className="panel">
        <div className="panel-header"><span className="panel-title">Component Status</span></div>
        <div className="panel-body compact">
          <div className="grid-3">
            {[
              { name: 'Tank Physics', status: 'ONLINE', detail: `Level: ${latest.true_level.toFixed(1)}%` },
              { name: 'Level Sensor LT-101', status: isSpoofed ? 'SPOOFED' : 'ONLINE', detail: `Reading: ${latest.sensor_level.toFixed(1)}%` },
              { name: 'Inflow Sensor FIT-101', status: 'ONLINE', detail: `${latest.inflow.toFixed(2)} %/s` },
              { name: 'Pump PUMP-101', status: latest.pump_state === 1 ? 'RUNNING' : 'STANDBY', detail: latest.pump_state === 1 ? 'Active' : 'Idle' },
              { name: 'Valve VALVE-101', status: latest.valve_state === 1 ? 'OPEN' : 'CLOSED', detail: latest.valve_state === 1 ? 'Discharging' : 'Holding' },
              { name: 'Virtual PLC', status: 'ONLINE', detail: `Mode: ${latest.plc_mode}` },
            ].map(c => (
              <div key={c.name} style={{ padding: '8px 0' }}>
                <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 2 }}>{c.name}</div>
                <span className={`badge ${c.status === 'SPOOFED' ? 'red' : c.status === 'ONLINE' || c.status === 'RUNNING' || c.status === 'OPEN' ? 'green' : 'gray'}`}>
                  {c.status}
                </span>
                <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 4 }}>{c.detail}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
