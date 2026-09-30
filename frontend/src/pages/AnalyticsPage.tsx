import React, { useEffect, useState } from 'react';
import { api } from '../api';
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer,
  AreaChart, Area, ReferenceLine
} from 'recharts';

function fmtTime(ts: number) {
  return new Date(ts * 1000).toLocaleTimeString(undefined, { hour12: false });
}

export default function AnalyticsPage() {
  const [data, setData] = useState<Record<string, unknown> | null>(null);
  const [experiments, setExperiments] = useState<Record<string, unknown>[]>([]);
  const [selectedExp, setSelectedExp] = useState<string>('');

  useEffect(() => {
    api.experiments.list().then(r => setExperiments(r)).catch(() => {});
  }, []);

  useEffect(() => {
    api.analytics.anomaly(selectedExp || undefined)
      .then(r => setData(r))
      .catch(() => {});
  }, [selectedExp]);

  const timeseries = (data?.timeseries as Record<string, unknown>[]) ?? [];
  const detections = (data?.detections as Record<string, unknown>[]) ?? [];

  const chartData = timeseries.slice(-1000).map(r => ({
    t: fmtTime(Number(r.timestamp)),
    true_level: Number(r.true_level),
    sensor_level: Number(r.sensor_level),
    residual: Number(r.process_residual),
    label: Number(r.label),
    attack: r.attack_type !== 'normal' ? Number(r.true_level) : null,
  }));

  const detChartData = detections.slice(-1000).map(r => ({
    t: fmtTime(Number(r.timestamp)),
    score: Number(r.anomaly_score),
    is_anomaly: Number(r.is_anomaly),
  }));

  return (
    <div>
      <div className="page-header">
        <div className="page-title">Analytics</div>
        <div className="page-sub">Historical anomaly detection and process analytics</div>
      </div>

      {/* Experiment filter */}
      <div style={{ marginBottom: 14, display: 'flex', alignItems: 'center', gap: 10 }}>
        <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>Experiment:</span>
        <select
          className="field-input"
          style={{ width: 280 }}
          value={selectedExp}
          onChange={e => setSelectedExp(e.target.value)}
        >
          <option value="">All Experiments</option>
          {experiments.map(e => (
            <option key={String(e.id)} value={String(e.id)}>
              {String(e.id)} — {String(e.name)}
            </option>
          ))}
        </select>
      </div>

      {timeseries.length === 0 ? (
        <div className="empty-state">
          No analytics data available. Run experiments to generate data.
        </div>
      ) : (
        <>
          {/* Level comparison */}
          <div className="panel" style={{ marginBottom: 12 }}>
            <div className="panel-header">
              <span className="panel-title">True vs Sensor Level — With Attack Periods</span>
              <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>{chartData.length} samples</span>
            </div>
            <div className="panel-body" style={{ padding: '12px 4px 4px' }}>
              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={chartData}>
                  <XAxis dataKey="t" tick={{ fontSize: 9, fill: 'var(--text-muted)' }} tickLine={false} axisLine={false} interval="preserveStartEnd" />
                  <YAxis domain={[0, 100]} tick={{ fontSize: 9, fill: 'var(--text-muted)' }} tickLine={false} axisLine={false} width={28} unit="%" />
                  <Tooltip contentStyle={{ background: 'var(--bg-overlay)', border: '1px solid var(--border)', borderRadius: 4, fontSize: 11 }} />
                  <Line type="monotone" dataKey="true_level" stroke="var(--chart-blue)" dot={false} strokeWidth={1.5} name="True Level" isAnimationActive={false} />
                  <Line type="monotone" dataKey="sensor_level" stroke="var(--chart-teal)" dot={false} strokeWidth={1.5} strokeDasharray="4 2" name="Sensor Level" isAnimationActive={false} />
                  <Line type="monotone" dataKey="attack" stroke="var(--chart-red)" dot={false} strokeWidth={1} strokeOpacity={0.3} name="Attack Period" isAnimationActive={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Anomaly score */}
          <div className="panel" style={{ marginBottom: 12 }}>
            <div className="panel-header">
              <span className="panel-title">ML Anomaly Score</span>
            </div>
            <div className="panel-body" style={{ padding: '12px 4px 4px' }}>
              <ResponsiveContainer width="100%" height={160}>
                <AreaChart data={detChartData}>
                  <XAxis dataKey="t" tick={{ fontSize: 9, fill: 'var(--text-muted)' }} tickLine={false} axisLine={false} interval="preserveStartEnd" />
                  <YAxis tick={{ fontSize: 9, fill: 'var(--text-muted)' }} tickLine={false} axisLine={false} width={40} />
                  <Tooltip contentStyle={{ background: 'var(--bg-overlay)', border: '1px solid var(--border)', borderRadius: 4, fontSize: 11 }} />
                  <Area type="monotone" dataKey="score" stroke="var(--chart-amber)" fill="rgba(245,158,11,0.1)" dot={false} strokeWidth={1.5} name="Anomaly Score" isAnimationActive={false} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Residual */}
          <div className="panel">
            <div className="panel-header">
              <span className="panel-title">Physical Residual Over Time</span>
            </div>
            <div className="panel-body" style={{ padding: '12px 4px 4px' }}>
              <ResponsiveContainer width="100%" height={140}>
                <AreaChart data={chartData}>
                  <XAxis dataKey="t" tick={{ fontSize: 9, fill: 'var(--text-muted)' }} tickLine={false} axisLine={false} interval="preserveStartEnd" />
                  <YAxis tick={{ fontSize: 9, fill: 'var(--text-muted)' }} tickLine={false} axisLine={false} width={28} />
                  <Tooltip contentStyle={{ background: 'var(--bg-overlay)', border: '1px solid var(--border)', borderRadius: 4, fontSize: 11 }} />
                  <ReferenceLine y={10} stroke="var(--color-red)" strokeDasharray="3 3" strokeOpacity={0.5} />
                  <Area type="monotone" dataKey="residual" stroke="var(--chart-red)" fill="rgba(239,68,68,0.08)" dot={false} strokeWidth={1.5} name="Residual" isAnimationActive={false} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
