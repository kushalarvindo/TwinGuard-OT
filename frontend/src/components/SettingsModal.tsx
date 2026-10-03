import React, { useState } from 'react';
import { X, Sliders, Activity, ShieldAlert, Lock, RefreshCw, CheckCircle, AlertTriangle } from 'lucide-react';
import { api } from '../api';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onForceResync?: () => void;
}

export default function SettingsModal({ isOpen, onClose, onForceResync }: Props) {
  const [activeTab, setActiveTab] = useState<'telemetry' | 'process' | 'thresholds' | 'safety'>('telemetry');
  const [autoRefresh, setAutoRefresh] = useState<boolean>(() => {
    return localStorage.getItem('twinguard_autorefresh') !== 'false';
  });
  const [cadence, setCadence] = useState<string>(() => {
    return localStorage.getItem('twinguard_cadence') || '3s';
  });
  const [recomputing, setRecomputing] = useState<boolean>(false);
  const [recomputeSuccess, setRecomputeSuccess] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleToggleAutoRefresh = (val: boolean) => {
    setAutoRefresh(val);
    localStorage.setItem('twinguard_autorefresh', String(val));
  };

  const handleCadenceChange = (val: string) => {
    setCadence(val);
    localStorage.setItem('twinguard_cadence', val);
  };

  const handleClearCache = () => {
    localStorage.clear();
    setRecomputeSuccess('Local client cache cleared successfully.');
    setTimeout(() => setRecomputeSuccess(null), 3000);
  };

  const handleRecompute = async () => {
    setRecomputing(true);
    setRecomputeSuccess(null);
    try {
      const res = await api.analytics.recompute();
      setRecomputeSuccess(res.status === 'SUCCESS' ? 'Evaluation recalculation completed! Metrics refreshed from database.' : 'Recalculation finished.');
      if (onForceResync) onForceResync();
    } catch (err: unknown) {
      setRecomputeSuccess(`Error: ${err instanceof Error ? err.message : String(err)}`);
    } finally {
      setRecomputing(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-container settings-modal" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="modal-header">
          <div>
            <div className="modal-category-chip">
              <span style={{ fontSize: 10 }}>⚙️</span>
              <span>CONTROL & CONFIGURATION</span>
            </div>
            <h2 className="modal-title">Platform Settings & Operational Parameters</h2>
            <p className="modal-desc">
              Configure real-time telemetry streaming, plant safety thresholds, physical process setpoints, and view the localhost safety enclosure.
            </p>
          </div>
          <button className="modal-close-btn" onClick={onClose} title="Close Settings">
            <X size={18} />
          </button>
        </div>

        {/* Tabs */}
        <div className="modal-tabs">
          <button
            className={`modal-tab ${activeTab === 'telemetry' ? 'active' : ''}`}
            onClick={() => setActiveTab('telemetry')}
          >
            <Activity size={14} />
            ⚡ Telemetry & Polling
          </button>
          <button
            className={`modal-tab ${activeTab === 'process' ? 'active' : ''}`}
            onClick={() => setActiveTab('process')}
          >
            <Sliders size={14} />
            🎛️ Process Setpoints
          </button>
          <button
            className={`modal-tab ${activeTab === 'thresholds' ? 'active' : ''}`}
            onClick={() => setActiveTab('thresholds')}
          >
            <ShieldAlert size={14} />
            🛡️ Anomaly Thresholds
          </button>
          <button
            className={`modal-tab ${activeTab === 'safety' ? 'active' : ''}`}
            onClick={() => setActiveTab('safety')}
          >
            <Lock size={14} />
            🔒 Localhost Isolation
          </button>
        </div>

        {/* Tab Content */}
        <div className="modal-body">
          {activeTab === 'telemetry' && (
            <div className="settings-section">
              <h4 className="settings-section-title">⚡ Real-Time Polling & Ingestion Cadence</h4>
              <p className="settings-section-desc">
                Control live dashboard synchronization with the industrial SQLite database and virtual PLC.
              </p>

              <div className="settings-grid-2">
                <div className="settings-card">
                  <div className="settings-card-label">Auto-Refresh Telemetry Stream</div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginTop: 8 }}>
                    <label className="switch">
                      <input
                        type="checkbox"
                        checked={autoRefresh}
                        onChange={(e) => handleToggleAutoRefresh(e.target.checked)}
                      />
                      <span className="slider round"></span>
                    </label>
                    <span style={{ fontSize: 13, color: autoRefresh ? 'var(--color-teal)' : 'var(--text-muted)' }}>
                      {autoRefresh ? 'Enabled (Active WebSocket / Polling)' : 'Paused'}
                    </span>
                  </div>
                </div>

                <div className="settings-card">
                  <div className="settings-card-label">Polling Cadence</div>
                  <div style={{ display: 'flex', gap: 6, marginTop: 8 }}>
                    {[
                      { id: '1s', label: '1s (Fast)' },
                      { id: '3s', label: '3s (Standard)' },
                      { id: '5s', label: '5s (Relaxed)' },
                    ].map(({ id, label }) => (
                      <button
                        key={id}
                        className={`btn-sm ${cadence === id ? 'btn-primary' : 'btn-secondary'}`}
                        onClick={() => handleCadenceChange(id)}
                      >
                        {label}
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              <div style={{ display: 'flex', gap: 10, marginTop: 14 }}>
                <button
                  className="btn-secondary"
                  onClick={() => {
                    if (onForceResync) onForceResync();
                    setRecomputeSuccess('Force resync triggered.');
                    setTimeout(() => setRecomputeSuccess(null), 2500);
                  }}
                >
                  <RefreshCw size={13} />
                  ⚡ Force Immediate Resync
                </button>
                <button className="btn-secondary" onClick={handleClearCache}>
                  🧹 Clear Local Storage Cache
                </button>
              </div>
            </div>
          )}

          {activeTab === 'process' && (
            <div className="settings-section">
              <h4 className="settings-section-title">🎛️ Plant Physical Setpoints & Limits</h4>
              <p className="settings-section-desc">
                Configured hysteresis thresholds governing virtual PLC automated pump and valve sequencing.
              </p>

              <div className="settings-metrics-3">
                <div className="settings-metric-card">
                  <div className="metric-label">Target Setpoint</div>
                  <div className="metric-value">70.0<span className="metric-unit">%</span></div>
                  <div className="metric-sub">Holding Register 40003</div>
                </div>
                <div className="settings-metric-card">
                  <div className="metric-label">High-Level Cutoff</div>
                  <div className="metric-value" style={{ color: 'var(--color-amber)' }}>
                    80.0<span className="metric-unit">%</span>
                  </div>
                  <div className="metric-sub">Pump auto-trips above this level</div>
                </div>
                <div className="settings-metric-card">
                  <div className="metric-label">Low-Level Refill</div>
                  <div className="metric-value" style={{ color: 'var(--color-teal)' }}>
                    30.0<span className="metric-unit">%</span>
                  </div>
                  <div className="metric-sub">Pump energizes below this level</div>
                </div>
              </div>

              <div className="settings-constants-box">
                <div className="constants-title">Tank Physical Model Constants (Hydrodynamic Equations):</div>
                <div className="constants-grid">
                  <div>• Max Height: <code>100.0 cm</code></div>
                  <div>• Tank Area: <code>1.20 m²</code></div>
                  <div>• Inflow Rate: <code>15.0 L/s</code></div>
                  <div>• Outflow Coeff: <code>0.60</code></div>
                  <div>• Sensor Noise σ: <code>0.15%</code></div>
                  <div>• Gravity g: <code>9.81 m/s²</code></div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'thresholds' && (
            <div className="settings-section">
              <h4 className="settings-section-title">🛡️ Anomaly Detection & Invariant Thresholds</h4>
              <p className="settings-section-desc">
                Deterministic residual bounds and Machine Learning contamination parameters.
              </p>

              <div className="settings-metrics-2">
                <div className="settings-metric-card">
                  <div className="metric-label">Residual Alarm Threshold</div>
                  <div className="metric-value" style={{ color: 'var(--color-red)' }}>5.0<span className="metric-unit">%</span></div>
                  <div className="metric-sub">R03: |h_sensor - h_shadow| &gt; 5%</div>
                </div>
                <div className="settings-metric-card">
                  <div className="metric-label">Command Flood Limit</div>
                  <div className="metric-value">30<span className="metric-unit">req/s</span></div>
                  <div className="metric-sub">R05: Packet frequency &gt; 30 req/s</div>
                </div>
                <div className="settings-metric-card">
                  <div className="metric-label">Critical Deviation Trip</div>
                  <div className="metric-value" style={{ color: 'var(--color-red)' }}>10.0<span className="metric-unit">%</span></div>
                  <div className="metric-sub">Emergency physical divergence trip</div>
                </div>
                <div className="settings-metric-card">
                  <div className="metric-label">Isolation Forest Contamination</div>
                  <div className="metric-value">0.10</div>
                  <div className="metric-sub">scikit-learn outlier fraction</div>
                </div>
              </div>

              <div style={{ marginTop: 16, paddingTop: 14, borderTop: '1px solid var(--border)' }}>
                <div style={{ fontWeight: 600, color: 'var(--text)', fontSize: 13, marginBottom: 4 }}>
                  Empirical Benchmark Verification
                </div>
                <p style={{ color: 'var(--text-muted)', fontSize: 12, margin: '0 0 10px 0' }}>
                  Recalculate mathematical evaluation metrics (Accuracy, Precision, Recall, F1) directly across stored ground-truth telemetry in the SQLite database.
                </p>
                <button
                  className="btn-primary"
                  onClick={handleRecompute}
                  disabled={recomputing}
                  style={{ width: '100%' }}
                >
                  <RefreshCw size={14} className={recomputing ? 'spin' : ''} />
                  {recomputing ? 'Calculating Actual Evaluation Metrics...' : '🔄 Recompute Evaluation Metrics Now'}
                </button>
              </div>
            </div>
          )}

          {activeTab === 'safety' && (
            <div className="settings-section">
              <div className="safety-notice-box">
                <div className="safety-notice-header">
                  <ShieldAlert size={16} />
                  <span>🛡️ Localhost Isolation Safety Notice</span>
                </div>
                <div className="safety-notice-body">
                  All packets, Modbus TCP transactions, red team attacks, and telemetry operate strictly inside virtual local memory (<code>127.0.0.1:5020</code>). 
                  External industrial systems, physical PLCs, SCADA networks, and remote hosts are completely isolated and will never be targeted.
                </div>
              </div>

              <div className="settings-grid-2">
                <div className="diagnostics-card">
                  <div className="diag-row"><span>MODBUS HOST:</span> <code>127.0.0.1</code></div>
                  <div className="diag-row"><span>MODBUS PORT:</span> <code>5020</code></div>
                  <div className="diag-row"><span>SLAVE / UNIT ID:</span> <code>1</code></div>
                  <div className="diag-row"><span>PLC SCAN RATE:</span> <span style={{ color: 'var(--color-green)', fontWeight: 700 }}>5.0 Hz (200ms)</span></div>
                </div>
                <div className="diagnostics-card">
                  <div className="diag-row"><span>DATABASE:</span> <span style={{ color: 'var(--color-blue)', fontWeight: 600 }}>SQLite (WAL Mode)</span></div>
                  <div className="diag-row"><span>PORT RANGE:</span> <code>8000 (API), 5173 (UI)</code></div>
                  <div className="diag-row"><span>ENVIRONMENT:</span> <span style={{ color: 'var(--color-purple)', fontWeight: 600 }}>Local Sandbox</span></div>
                  <div className="diag-row"><span>SAFETY STATUS:</span> <span style={{ color: 'var(--color-green)', fontWeight: 700 }}>ENCLOSED</span></div>
                </div>
              </div>
            </div>
          )}

          {recomputeSuccess && (
            <div className="feedback-banner" style={{ marginTop: 14 }}>
              {recomputeSuccess.startsWith('Error') ? (
                <AlertTriangle size={15} style={{ color: 'var(--color-red)' }} />
              ) : (
                <CheckCircle size={15} style={{ color: 'var(--color-teal)' }} />
              )}
              <span>{recomputeSuccess}</span>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="modal-footer" style={{ justifyContent: 'flex-end' }}>
          <button className="btn-primary" onClick={onClose}>
            Done & Close Settings
          </button>
        </div>
      </div>
    </div>
  );
}
