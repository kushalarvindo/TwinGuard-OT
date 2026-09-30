import React, { useEffect, useState } from 'react';
import { api } from '../api';
import type { EvaluationResult } from '../types';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend, CartesianGrid } from 'recharts';

export default function EvaluationPage() {
  const [results, setResults] = useState<EvaluationResult[]>([]);

  useEffect(() => {
    api.analytics.evaluation().then(r => setResults(r as EvaluationResult[])).catch(() => {});
  }, []);

  const chartData = results.map(r => ({
    name: r.experiment_id.replace('EXP-', ''),
    Accuracy: Number(r.accuracy) * 100,
    Precision: Number(r.precision) * 100,
    Recall: Number(r.recall) * 100,
    F1: Number(r.f1_score) * 100,
  }));

  return (
    <div>
      <div className="page-header">
        <div className="page-title">Evaluation Metrics</div>
        <div className="page-sub">Global benchmark performance across all recorded attack experiments</div>
      </div>

      {results.length === 0 ? (
        <div className="empty-state">No evaluation metrics computed yet. Run the full experiment suite.</div>
      ) : (
        <>
          {/* Chart */}
          <div className="panel" style={{ marginBottom: 14 }}>
            <div className="panel-header"><span className="panel-title">Detection Performance (%)</span></div>
            <div className="panel-body">
              <ResponsiveContainer width="100%" height={240}>
                <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="name" tick={{ fontSize: 10, fill: 'var(--text-muted)' }} axisLine={false} tickLine={false} />
                  <YAxis domain={[0, 100]} tick={{ fontSize: 10, fill: 'var(--text-muted)' }} axisLine={false} tickLine={false} />
                  <Tooltip
                    contentStyle={{ background: 'var(--bg-overlay)', border: '1px solid var(--border)', borderRadius: 4, fontSize: 11 }}
                    cursor={{ fill: 'var(--bg-hover)' }}
                    formatter={(val: number) => [val.toFixed(1) + '%']}
                  />
                  <Legend wrapperStyle={{ fontSize: 11 }} />
                  <Bar dataKey="Accuracy" fill="var(--chart-blue)" radius={[2, 2, 0, 0]} />
                  <Bar dataKey="Precision" fill="var(--chart-teal)" radius={[2, 2, 0, 0]} />
                  <Bar dataKey="Recall" fill="var(--chart-amber)" radius={[2, 2, 0, 0]} />
                  <Bar dataKey="F1" fill="var(--chart-purple)" radius={[2, 2, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Table */}
          <div className="panel">
            <div className="panel-header"><span className="panel-title">Detailed Results</span></div>
            <div className="panel-body no-pad">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Experiment</th>
                    <th>Model</th>
                    <th>Samples</th>
                    <th>Accuracy</th>
                    <th>Precision</th>
                    <th>Recall</th>
                    <th>F1 Score</th>
                    <th>FPR</th>
                    <th>Latency (s)</th>
                  </tr>
                </thead>
                <tbody>
                  {results.map((r, i) => (
                    <tr key={i}>
                      <td style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{r.experiment_id}</td>
                      <td className="mono">{r.model_name}</td>
                      <td className="mono">{r.total_samples}</td>
                      <td className="mono" style={{ color: 'var(--color-blue)' }}>{(Number(r.accuracy) * 100).toFixed(1)}%</td>
                      <td className="mono" style={{ color: 'var(--color-teal)' }}>{(Number(r.precision) * 100).toFixed(1)}%</td>
                      <td className="mono" style={{ color: 'var(--color-amber)' }}>{(Number(r.recall) * 100).toFixed(1)}%</td>
                      <td className="mono" style={{ color: 'var(--color-purple)' }}>{(Number(r.f1_score) * 100).toFixed(1)}%</td>
                      <td className="mono" style={{ color: 'var(--color-red)' }}>{(Number(r.false_positive_rate) * 100).toFixed(2)}%</td>
                      <td className="mono">{r.detection_latency_sec ? Number(r.detection_latency_sec).toFixed(2) : '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
