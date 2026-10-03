import React from 'react';
import type { TelemetryFrame } from '../types';
import type { PageId } from '../App';
import { Compass, Settings as SettingsIcon, AlertCircle } from 'lucide-react';

interface Props {
  connected: boolean;
  latest: TelemetryFrame | null;
  currentPage: PageId;
  onOpenTour: () => void;
  onOpenSettings: () => void;
}

const PAGE_META: Record<PageId, { title: string; desc: string }> = {
  overview: {
    title: 'Process SCADA Overview',
    desc: 'Live water tank level, pump/valve telemetry, and closed-loop hysteresis control.',
  },
  twin: {
    title: 'Digital Twin Shadow Model',
    desc: 'Hydrodynamic mass-balance model and continuous residual r(t) = |h_sensor - h_shadow|.',
  },
  telemetry: {
    title: 'Live Telemetry Stream',
    desc: 'High-frequency sensor and actuator time-series telemetry inspection.',
  },
  modbus: {
    title: 'Modbus Protocol Inspector',
    desc: 'Transaction logging, register memory map, and packet arrival rate tracking (port 5020).',
  },
  attacks: {
    title: 'Cyberattack Laboratory',
    desc: 'Isolated localhost threat injection and red team attack scenarios against virtual PLC.',
  },
  detection: {
    title: 'Multi-Tier Anomaly Detection',
    desc: 'Domain invariant rules, hydrodynamic shadow model, and Isolation Forest ML.',
  },
  analytics: {
    title: 'Statistical Process Analytics',
    desc: 'Sensor drift, residual error distributions, and physical actuator correlation.',
  },
  experiments: {
    title: 'Automated Experiment Runner',
    desc: 'Orchestrate controlled cyberattack experiments across warmup, attack, and cooldown phases.',
  },
  evaluation: {
    title: 'Empirical Evaluation Metrics',
    desc: 'Precision, Recall, F1-Score, and FPR verification against ground-truth datasets.',
  },
  datasets: {
    title: 'Datasets & Research Artifacts',
    desc: 'Recorded telemetry logs, experiment filtering, and CSV export for research reports.',
  },
  system: {
    title: 'System Health & Architecture',
    desc: 'Localhost sandbox runtime status, component connectivity, and process diagnostics.',
  },
};

function Dot({ color, pulse }: { color: string; pulse?: boolean }) {
  return <span className={`status-dot ${color}${pulse ? ' pulse' : ''}`} />;
}

export default function Header({
  connected,
  latest,
  currentPage,
  onOpenTour,
  onOpenSettings,
}: Props) {
  const modbusOk = connected;
  const detectionOk = connected;
  const hasAttack = Boolean(latest?.active_attack);
  const isAnomaly = Boolean(latest?.is_anomaly || (latest && latest.residual > 5.0));
  const residual = latest?.residual ?? 0.0;
  const expId = latest?.experiment_id || 'EXP-BASELINE-NORMAL';

  const meta = PAGE_META[currentPage] || {
    title: 'TwinGuard-OT SCADA',
    desc: 'Industrial Cyber-Physical Platform',
  };

  return (
    <header className="header">
      <div className="header-left">
        <div className="header-breadcrumbs">
          <div className="header-crumb-row">
            <span className="header-brand-tag">TWINGUARD-OT</span>
            <span className="header-crumb-sep">/</span>
            <h1 className="header-view-title">{meta.title}</h1>
          </div>
          <p className="header-view-desc">{meta.desc}</p>
        </div>
      </div>

      <div className="header-right">
        {hasAttack && (
          <span className="badge red header-attack-badge">
            <AlertCircle size={12} />
            <span>ATTACK ACTIVE: {latest?.active_attack?.replace(/_/g, ' ').toUpperCase()}</span>
          </span>
        )}

        <div className="header-status-group">
          {isAnomaly ? (
            <span className="chip-status-alert">
              <Dot color="red" pulse />
              ALERT
            </span>
          ) : (
            <span className="chip-status-normal">
              <Dot color="green" />
              NORMAL
            </span>
          )}

          <span className="header-tech-pill">{expId}</span>

          <span
            className="header-residual-readout"
            style={{ color: residual > 5.0 ? 'var(--color-red)' : 'var(--color-green)' }}
          >
            |r| = {residual.toFixed(1)}%
          </span>
        </div>

        <div className="header-pill-group">
          <span className="status-pill">
            <Dot color={connected ? 'green' : 'red'} pulse={!connected} />
            {connected ? 'Operational' : 'Disconnected'}
          </span>
          <span className="status-pill">
            <Dot color={modbusOk ? 'green' : 'amber'} />
            Modbus
          </span>
          <span className="status-pill">
            <Dot color={detectionOk ? 'green' : 'amber'} />
            Detection
          </span>
        </div>

        <div className="header-actions">
          <button
            className="header-action-btn"
            onClick={onOpenTour}
            title="Open Platform Onboarding Tour"
          >
            <Compass size={14} />
            <span>Tour</span>
          </button>
          <button
            className="header-action-btn"
            onClick={onOpenSettings}
            title="Open Platform Settings & Safety Controls"
          >
            <SettingsIcon size={14} />
            <span>Settings</span>
          </button>
        </div>
      </div>
    </header>
  );
}
