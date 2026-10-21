import React, { useState } from 'react';
import type { TelemetryFrame } from '../types';
import { useTelemetry } from '../hooks/useTelemetry';
import {
  AreaChart, Area, LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine
} from 'recharts';
import { Zap, Box, Layers } from 'lucide-react';
import ThreeTankRig from '../components/ThreeTankRig';

interface Props {
  telemetry: ReturnType<typeof useTelemetry>;
}

function TankVisualization({ frame }: { frame: TelemetryFrame }) {
  const trueH = Math.max(0, Math.min(100, frame.true_level));
  const sensorH = Math.max(0, Math.min(100, frame.sensor_level));
  const delta = Math.abs(trueH - sensorH);
  const isDiverged = delta > 5.0 || frame.sensor_spoofed;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12 }}>
      {/* Top Synchronization Delta Badge */}
      <div style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 8,
        padding: '3px 10px',
        borderRadius: 9999,
        fontSize: 11,
        background: isDiverged ? 'rgba(239, 68, 68, 0.12)' : 'rgba(56, 189, 248, 0.10)',
        border: `1px solid ${isDiverged ? 'rgba(239, 68, 68, 0.35)' : 'rgba(56, 189, 248, 0.25)'}`,
        color: isDiverged ? 'var(--color-red)' : 'var(--color-teal)',
        fontFamily: "'JetBrains Mono', monospace",
        fontWeight: 600,
      }}>
        <span>{isDiverged ? '⚡ SENSOR / GROUND-TRUTH DIVERGENCE' : '✔ PROCESS SYNCHRONIZED'}</span>
        <span>•</span>
        <span>Δ = {delta.toFixed(2)}%</span>
      </div>

      <div className="tank-wrapper">
        {/* Pump */}
        <div className="flow-component" style={{ alignItems: 'flex-end', paddingBottom: 80 }}>
          <div className={`flow-box ${frame.pump_state === 1 ? 'online' : 'offline'}`} style={{ minWidth: 64 }}>
            PUMP
          </div>
          <div className="flow-label" style={{ marginTop: 4 }}>
            {frame.pump_state === 1 ? 'ON (15 L/s)' : 'IDLE'}
          </div>
        </div>

        {/* Calibrated Scale */}
        <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between', height: 160, padding: '4px 0', fontSize: 9, color: 'var(--text-muted)', fontFamily: 'monospace', textAlign: 'right', marginRight: 4 }}>
          <span>100%</span>
          <span style={{ color: 'var(--color-amber)' }}>80% (H)</span>
          <span style={{ color: 'var(--color-green)' }}>70% (SP)</span>
          <span style={{ color: 'var(--color-blue)' }}>30% (L)</span>
          <span>0%</span>
        </div>

        {/* True Level Tank */}
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
          <div style={{ fontSize: 10, color: 'var(--text-muted)', fontWeight: 600, letterSpacing: '0.05em' }}>TRUE LEVEL</div>
          <div className="tank-body">
            <div
              className="tank-fill true"
              style={{ height: `${trueH}%` }}
            />
            {/* Threshold lines */}
            <div
              className="threshold-line high"
              style={{ bottom: `${frame.high_threshold}%` }}
              title="High Threshold (80%)"
            />
            <div
              className="threshold-line low"
              style={{ bottom: `${frame.low_threshold}%` }}
              title="Low Threshold (30%)"
            />
            <div
              className="threshold-line setpoint"
              style={{ bottom: `${frame.setpoint}%` }}
              title="Target Setpoint (70%)"
            />
          </div>
          <div className="tank-value" style={{ color: 'var(--color-blue)' }}>{trueH.toFixed(1)}%</div>
        </div>

        {/* Sensor Level Tank */}
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
          <div style={{ fontSize: 10, color: 'var(--text-muted)', fontWeight: 600, letterSpacing: '0.05em' }}>SENSOR READ</div>
          <div className="tank-body" style={{ borderColor: isDiverged ? 'rgba(239,68,68,0.5)' : undefined }}>
            <div
              className="tank-fill sensor"
              style={{
                height: `${sensorH}%`,
                background: isDiverged ? 'linear-gradient(180deg, #f87171 0%, #ef4444 100%)' : undefined,
              }}
            />
          </div>
          <div
            className="tank-value"
            style={{ color: isDiverged ? 'var(--color-red)' : 'var(--color-teal)' }}
          >
            {sensorH.toFixed(1)}%
            {frame.sensor_spoofed && <span style={{ fontSize: 9, marginLeft: 4, fontWeight: 700 }}>SPOOFED</span>}
          </div>
        </div>

        {/* Valve */}
        <div className="flow-component" style={{ alignItems: 'flex-start', paddingBottom: 80 }}>
          <div className={`flow-box ${frame.valve_state === 1 ? 'online' : 'offline'}`} style={{ minWidth: 64 }}>
            VALVE
          </div>
          <div className="flow-label" style={{ marginTop: 4 }}>
            {frame.valve_state === 1 ? 'OPEN (Gravity)' : 'CLOSED'}
          </div>
        </div>
      </div>
    </div>
  );
}

function fmtTime(ts: number) {
  return new Date(ts * 1000).toLocaleTimeString(undefined, { hour12: false });
}

export default function OverviewPage({ telemetry }: Props) {
  const { latest, history } = telemetry;
  const [rigViewMode, setRigViewMode] = useState<'3d' | '2d'>('3d');

  if (!latest) {
    return (
      <div className="loading-state">
        <div className="spinner" />
        Connecting to simulation...
      </div>
    );
  }

  const activeAttack = latest.active_attack;
  const chartData = history.slice(-150).map(f => ({
    t: fmtTime(f.timestamp),
    true_level: f.true_level,
    sensor_level: f.sensor_level,
    anomaly_score: f.anomaly_score,
  }));

  const alarmText = ['NORMAL', 'LOW LEVEL', 'HIGH LEVEL', 'SAFETY INTERLOCK'][latest.alarm_state] ?? 'NORMAL';

  return (
    <div>
      <div className="page-header">
        <div className="page-title">Overview</div>
        <div className="page-sub">Real-time digital twin process state and security status</div>
      </div>

      {activeAttack && (
        <div className="attack-active-banner">
          <Zap size={14} />
          <strong>ATTACK ACTIVE:</strong>&nbsp;
          {activeAttack.replace(/_/g, ' ').toUpperCase()}
          &nbsp;— Monitoring for anomalies
        </div>
      )}

      {/* Key metrics row */}
      <div className="grid-4" style={{ marginBottom: 14 }}>
        <div className="metric-card">
          <div className="metric-label">True Level</div>
          <div className="metric-value">
            {latest.true_level.toFixed(1)}
            <span className="metric-unit">%</span>
          </div>
          <div className="metric-sub">Setpoint: {latest.setpoint.toFixed(0)}%</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Sensor Level</div>
          <div className="metric-value" style={{ color: latest.sensor_spoofed ? 'var(--color-red)' : undefined }}>
            {latest.sensor_level.toFixed(1)}
            <span className="metric-unit">%</span>
          </div>
          <div className="metric-sub">
            {latest.sensor_spoofed
              ? <span style={{ color: 'var(--color-red)' }}>⚠ SPOOFED</span>
              : `Residual: ${latest.residual.toFixed(1)}%`}
          </div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Anomaly Score</div>
          <div className="metric-value" style={{ color: latest.is_anomaly ? 'var(--color-red)' : 'var(--color-green)' }}>
            {latest.anomaly_score.toFixed(3)}
          </div>
          <div className="metric-sub">
            {latest.is_anomaly
              ? <span style={{ color: 'var(--color-red)' }}>ANOMALY DETECTED</span>
              : <span style={{ color: 'var(--color-green)' }}>Normal</span>}
          </div>
        </div>
        <div className="metric-card">
          <div className="metric-label">PLC Alarm</div>
          <div className="metric-value" style={{ fontSize: 14, color: latest.alarm_state > 0 ? 'var(--color-amber)' : 'var(--color-green)' }}>
            {alarmText}
          </div>
          <div className="metric-sub">Mode: {latest.plc_mode}</div>
        </div>
      </div>

      {/* Tank viz + chart */}
      <div className="grid-2-1" style={{ marginBottom: 14 }}>
        <div className="panel">
          <div className="panel-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span className="panel-title">Live Physical Process — Water Storage Rig</span>
              <span className="badge blue">LIVE</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
              <button
                className={`btn-sm ${rigViewMode === '3d' ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => setRigViewMode('3d')}
                style={{ height: 24, fontSize: 11, padding: '0 8px', display: 'inline-flex', alignItems: 'center', gap: 4 }}
              >
                <Box size={12} />
                <span>3D Digital Twin</span>
              </button>
              <button
                className={`btn-sm ${rigViewMode === '2d' ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => setRigViewMode('2d')}
                style={{ height: 24, fontSize: 11, padding: '0 8px', display: 'inline-flex', alignItems: 'center', gap: 4 }}
              >
                <Layers size={12} />
                <span>2D Schematic</span>
              </button>
            </div>
          </div>
          <div className="panel-body no-pad" style={{ padding: rigViewMode === '3d' ? 0 : 16 }}>
            {rigViewMode === '3d' ? (
              <ThreeTankRig frame={latest} height={360} />
            ) : (
              <>
                <TankVisualization frame={latest} />
                {/* Threshold legend */}
                <div style={{ display: 'flex', gap: 16, justifyContent: 'center', marginTop: 12 }}>
                  {[
                    { label: 'Low (30%)', color: 'var(--color-blue)' },
                    { label: 'Setpoint (70%)', color: 'var(--color-green)' },
                    { label: 'High (80%)', color: 'var(--color-amber)' },
                  ].map(t => (
                    <span key={t.label} style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 10, color: 'var(--text-muted)' }}>
                      <span style={{ width: 14, height: 1, background: t.color, display: 'inline-block' }} />
                      {t.label}
                    </span>
                  ))}
                </div>
              </>
            )}
          </div>
        </div>

        <div className="panel">
          <div className="panel-header">
            <span className="panel-title">Process Status</span>
          </div>
          <div className="panel-body">
            <table style={{ width: '100%', fontSize: 12, borderCollapse: 'collapse' }}>
              <tbody>
                {[
                  { label: 'Pump', value: latest.pump_state === 1 ? 'ON' : 'OFF', color: latest.pump_state === 1 ? 'var(--color-green)' : 'var(--text-secondary)' },
                  { label: 'Valve', value: latest.valve_state === 1 ? 'OPEN' : 'CLOSED', color: latest.valve_state === 1 ? 'var(--color-blue)' : 'var(--text-secondary)' },
                  { label: 'Inflow', value: `${latest.inflow.toFixed(2)} %/s`, color: 'var(--text-primary)' },
                  { label: 'Outflow', value: `${latest.outflow.toFixed(2)} %/s`, color: 'var(--text-primary)' },
                  { label: 'Residual', value: `${latest.residual.toFixed(2)}%`, color: latest.residual > 10 ? 'var(--color-red)' : 'var(--text-primary)' },
                  { label: 'Request Rate', value: `${latest.request_rate.toFixed(1)} r/s`, color: latest.request_rate > 30 ? 'var(--color-amber)' : 'var(--text-primary)' },
                  { label: 'Overflow', value: latest.is_overflow ? 'YES' : 'No', color: latest.is_overflow ? 'var(--color-red)' : 'var(--text-secondary)' },
                ].map(row => (
                  <tr key={row.label}>
                    <td style={{ padding: '6px 0', color: 'var(--text-muted)', fontWeight: 500 }}>{row.label}</td>
                    <td style={{ padding: '6px 0', color: row.color, textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>{row.value}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Time-series charts */}
      <div className="grid-2" style={{ marginBottom: 14 }}>
        <div className="panel">
          <div className="panel-header">
            <span className="panel-title">Tank Level</span>
            <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>True vs Sensor</span>
          </div>
          <div className="panel-body" style={{ padding: '10px 4px 4px' }}>
            <ResponsiveContainer width="100%" height={120}>
              <LineChart data={chartData}>
                <XAxis dataKey="t" tick={{ fontSize: 9, fill: 'var(--text-muted)' }} tickLine={false} axisLine={false} interval="preserveStartEnd" />
                <YAxis domain={[0, 100]} tick={{ fontSize: 9, fill: 'var(--text-muted)' }} tickLine={false} axisLine={false} width={28} />
                <Tooltip contentStyle={{ background: 'var(--bg-overlay)', border: '1px solid var(--border)', borderRadius: 4, fontSize: 11 }} />
                <ReferenceLine y={latest.high_threshold} stroke="var(--color-amber)" strokeDasharray="3 3" strokeOpacity={0.4} />
                <ReferenceLine y={latest.setpoint} stroke="var(--color-green)" strokeDasharray="3 3" strokeOpacity={0.4} />
                <Line type="monotone" dataKey="true_level" stroke="var(--chart-blue)" dot={false} strokeWidth={1.5} name="True" isAnimationActive={false} />
                <Line type="monotone" dataKey="sensor_level" stroke="var(--chart-teal)" dot={false} strokeWidth={1.5} strokeDasharray="4 2" name="Sensor" isAnimationActive={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="panel">
          <div className="panel-header">
            <span className="panel-title">Anomaly Score</span>
            <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>ML Detection</span>
          </div>
          <div className="panel-body" style={{ padding: '10px 4px 4px' }}>
            <ResponsiveContainer width="100%" height={120}>
              <AreaChart data={chartData}>
                <XAxis dataKey="t" tick={{ fontSize: 9, fill: 'var(--text-muted)' }} tickLine={false} axisLine={false} interval="preserveStartEnd" />
                <YAxis tick={{ fontSize: 9, fill: 'var(--text-muted)' }} tickLine={false} axisLine={false} width={36} />
                <Tooltip contentStyle={{ background: 'var(--bg-overlay)', border: '1px solid var(--border)', borderRadius: 4, fontSize: 11 }} />
                <Area type="monotone" dataKey="anomaly_score" stroke="var(--chart-amber)" fill="rgba(245,158,11,0.1)" dot={false} strokeWidth={1.5} name="Score" isAnimationActive={false} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}
