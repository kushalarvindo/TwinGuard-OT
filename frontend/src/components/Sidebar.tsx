import React from 'react';
import type { PageId } from '../App';
import {
  LayoutDashboard, Activity, Cpu, Radio, Zap, ShieldAlert,
  BarChart2, FlaskConical, ClipboardCheck, Database, Settings as SettingsIcon,
  Shield, Compass
} from 'lucide-react';

interface NavSection {
  title: string;
  items: {
    id: PageId;
    label: string;
    Icon: React.FC<{ size?: number }>;
    badge?: string;
  }[];
}

const SECTIONS: NavSection[] = [
  {
    title: 'SCADA OPERATIONS',
    items: [
      { id: 'overview',  label: 'Process SCADA Overview', Icon: LayoutDashboard },
      { id: 'twin',      label: 'Digital Twin Shadow',    Icon: Cpu },
      { id: 'telemetry', label: 'Live Telemetry',         Icon: Activity },
      { id: 'modbus',    label: 'Modbus Protocol Monitor',Icon: Radio },
    ],
  },
  {
    title: 'THREAT INTELLIGENCE',
    items: [
      { id: 'attacks',   label: 'Cyberattack Laboratory', Icon: Zap },
      { id: 'detection', label: 'Multi-Tier Anomaly SOC', Icon: ShieldAlert },
    ],
  },
  {
    title: 'ANALYTICS & BENCHMARKS',
    items: [
      { id: 'analytics',   label: 'Process Analytics',     Icon: BarChart2 },
      { id: 'experiments', label: 'Experiment Runner',    Icon: FlaskConical },
      { id: 'evaluation',  label: 'Evaluation Metrics',   Icon: ClipboardCheck },
      { id: 'datasets',    label: 'Datasets & Export',     Icon: Database },
    ],
  },
  {
    title: 'PLATFORM CONTROL',
    items: [
      { id: 'system',      label: 'System Health',         Icon: SettingsIcon },
    ],
  },
];

interface Props {
  currentPage: PageId;
  onNavigate: (p: PageId) => void;
  onOpenSettings?: () => void;
  onOpenTour?: () => void;
}

export default function Sidebar({ currentPage, onNavigate, onOpenSettings, onOpenTour }: Props) {
  return (
    <aside className="sidebar">
      {/* Brand Header */}
      <div className="sidebar-brand">
        <div className="sidebar-brand-icon">
          <Shield size={20} />
        </div>
        <div>
          <div className="sidebar-brand-name">TwinGuard-OT</div>
          <div className="sidebar-brand-sub">ICS DIGITAL TWIN v2.2</div>
        </div>
      </div>

      {/* Grouped Navigation */}
      <nav className="sidebar-nav">
        {SECTIONS.map((sec) => (
          <div key={sec.title} className="sidebar-nav-section">
            <div className="sidebar-section-label">{sec.title}</div>
            {sec.items.map(({ id, label, Icon, badge }) => (
              <button
                key={id}
                className={`nav-item${currentPage === id ? ' active' : ''}`}
                onClick={() => onNavigate(id)}
              >
                <Icon size={14} />
                <span className="nav-item-label">{label}</span>
                {badge && <span className="nav-item-badge">{badge}</span>}
              </button>
            ))}
          </div>
        ))}

        {/* Quick Modal Actions */}
        <div className="sidebar-nav-section">
          <div className="sidebar-section-label">QUICK ACTIONS</div>
          <div className="sidebar-quick-actions">
            {onOpenSettings && (
              <button className="sidebar-action-btn" onClick={onOpenSettings} title="Settings">
                <SettingsIcon size={13} />
                <span>Settings</span>
              </button>
            )}
            {onOpenTour && (
              <button className="sidebar-action-btn" onClick={onOpenTour} title="Platform Tour">
                <Compass size={13} />
                <span>Tour</span>
              </button>
            )}
          </div>
        </div>
      </nav>

      {/* System Status Diagnostics Dock */}
      <div className="sidebar-footer">
        <div className="sidebar-diagnostics-dock">
          <div className="dock-row">
            <span className="dock-label">MODBUS:</span>
            <code className="dock-val">127.0.0.1:5020</code>
          </div>
          <div className="dock-row">
            <span className="dock-label">PLC RATE:</span>
            <span className="dock-val" style={{ color: 'var(--color-green)', fontWeight: 700 }}>5.0 Hz (200ms)</span>
          </div>
          <div className="dock-row">
            <span className="dock-label">STORAGE:</span>
            <span className="dock-val" style={{ color: 'var(--color-blue)', fontWeight: 600 }}>SQLite (WAL Active)</span>
          </div>
        </div>
      </div>
    </aside>
  );
}
