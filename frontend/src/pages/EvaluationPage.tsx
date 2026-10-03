import React, { useEffect, useState } from 'react';
import { api } from '../api';
import type { EvaluationResult } from '../types';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend, CartesianGrid } from 'recharts';
import { RefreshCw, CheckCircle, AlertTriangle } from 'lucide-react';

export default function EvaluationPage() {
  const [results, setResults] = useState<EvaluationResult[]>([]);
  const [recomputing, setRecomputing] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);

  const fetchResults = () => {
    api.analytics.evaluation()
      .then(r => setResults(r as EvaluationResult[]))
      .catch(() => {});
  };

  useEffect(() => {
    fetchResults();
  }, []);

  const handleRecompute = async () => {
    setRecomputing(true);
    setFeedback(null);
    try {
      const res = await api.analytics.recompute();
      if (res.status === 'SUCCESS') {
        setFeedback('Evaluation metrics recalculated successfully from ground-truth database.');
        fetchResults();
      } else {
        setFeedback(`Notice: ${res.detail || 'Recalculation complete.'}`);
      }
    } catch (err: unknown) {
      setFeedback(`Error recalculating: ${err instanceof Error ? err.message : String(err)}`);
    } finally {
      setRecomputing(false);
    }
  };

  const chartData = results.map(r => ({
    name: r.experiment_id.replace('EXP-', ''),
    Accuracy: Number(r.accuracy) * 100,
    Precision: Number(r.precision) * 100,
    Recall: Number(r.recall) * 100,
    F1: Number(r.f1_score) * 100,
  }));

  // Calculate averages across models
  const avgAcc = results.length > 0
    ? (results.reduce((acc, r) => acc + Number(r.accuracy), 0) / results.length) * 100
    : 0;
  const avgPrec = results.length > 0
    ? (results.reduce((acc, r) => acc + Number(r.precision), 0) / results.length) * 100
    : 0;
  const avgRec = results.length > 0
    ? (results.reduce((acc, r) => acc + Number(r.recall), 0) / results.length) * 100
    : 0;
  const avgF1 = results.length > 0
    ? (results.reduce((acc, r) => acc + Number(r.f1_score), 0) / results.length) * 100
    : 0;

  return (
    <div>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <div className="page-title">Evaluation Metrics</div>
          <div className="page-sub">Global benchmark performance across all recorded attack experiments</div>
        </div>
        <button
          className="btn-primary"
          onClick={handleRecompute}
          disabled={recomputing}
          style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}
        >
          <RefreshCw size={14} className={recomputing ? 'spin' : ''} />
          {recomputing ? 'Recalculating...' : '🔄 Recompute Metrics Now'}
        </button>
      </div>

      {feedback && (
        <div className="feedback-banner" style={{ marginBottom: 14 }}>
          {feedback.startsWith('Error') ? (
            <AlertTriangle size={15} style={{ color: 'var(--color-red)' }} />
          ) : (
            <CheckCircle size={15} style={{ color: 'var(--color-teal)' }} />
          )}
          <span>{feedback}</span>
        </div>
      )}

      {results.length > 0 && (
        <div className="grid-4" style={{ marginBottom: 14 }}>
          <div className="metric-card">
            <div className="metric-label">Benchmark Accuracy</div>
            <div className="metric-value" style={{ color: 'var(--color-blue)' }}>
              {avgAcc.toFixed(1)}<span className="metric-unit">%</span>
            </div>
            <div className="metric-sub">Mean across {results.length} evaluations</div>
          </div>
          <div className="metric-card">
            <div className="metric-label">Precision Rate</div>
            <div className="metric-value" style={{ color: 'var(--color-teal)' }}>
              {avgPrec.toFixed(1)}<span className="metric-unit">%</span>
            </div>
            <div className="metric-sub">True Positive / Total Detected</div>
          </div>
          <div className="metric-card">
            <div className="metric-label">Recall Coverage</div>
            <div className="metric-value" style={{ color: 'var(--color-amber)' }}>
              {avgRec.toFixed(1)}<span className="metric-unit">%</span>
            </div>
            <div className="metric-sub">Attacks Captured / Total Attacks</div>
          </div>
          <div className="metric-card">
            <div className="metric-label">Harmonic F1-Score</div>
            <div className="metric-value" style={{ color: 'var(--color-purple)' }}>
              {avgF1.toFixed(1)}<span className="metric-unit">%</span>
            </div>
            <div className="metric-sub">Balanced Detection Efficacy</div>
          </div>
        </div>
      )}

      {results.length === 0 ? (
        <div className="empty-state">
          <div>No evaluation metrics computed yet.</div>
          <button className="btn-secondary" onClick={handleRecompute} style={{ marginTop: 10 }}>
            Run Benchmark Evaluation Pipeline
          </button>
        </div>
      ) : (
        <>
          {/* Chart */}
          <div className="panel" style={{ marginBottom: 14 }}>
            <div className="panel-header">
              <span className="panel-title">Detection Performance Across Experiments (%)</span>
            </div>
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
            <div className="panel-header">
              <span className="panel-title">Empirical Benchmark Verification Table</span>
            </div>
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
