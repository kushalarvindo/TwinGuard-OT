import React from 'react';
import type { PageId } from '../App';
import {
  LayoutDashboard, Activity, Cpu, Radio, Zap, ShieldAlert,
  BarChart2, FlaskConical, ClipboardCheck, Database, Settings
} from 'lucide-react';

interface NavItem { id: PageId; label: string; Icon: React.FC<{ size?: number }> }

const NAV_ITEMS: NavItem[] = [
  { id: 'overview',    label: 'Overview',         Icon: LayoutDashboard },
  { id: 'twin',        label: 'Digital Twin',      Icon: Cpu },
  { id: 'telemetry',   label: 'Live Telemetry',    Icon: Activity },
  { id: 'modbus',      label: 'Modbus Monitor',    Icon: Radio },
  { id: 'attacks',     label: 'Attack Simulator',  Icon: Zap },
  { id: 'detection',   label: 'Detection & Alerts',Icon: ShieldAlert },
  { id: 'analytics',   label: 'Analytics',         Icon: BarChart2 },
  { id: 'experiments', label: 'Experiments',        Icon: FlaskConical },
  { id: 'evaluation',  label: 'Evaluation',         Icon: ClipboardCheck },
  { id: 'datasets',    label: 'Datasets',           Icon: Database },
  { id: 'system',      label: 'System Health',      Icon: Settings },
];

interface Props {
  currentPage: PageId;
  onNavigate: (p: PageId) => void;
}

export default function Sidebar({ currentPage, onNavigate }: Props) {
  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="sidebar-brand-name">TwinGuard-OT</div>
        <div className="sidebar-brand-sub">ICS Cybersecurity Platform</div>
      </div>

      <span className="sidebar-section-label">Navigation</span>

      <nav className="sidebar-nav">
        {NAV_ITEMS.map(({ id, label, Icon }) => (
          <button
            key={id}
            className={`nav-item${currentPage === id ? ' active' : ''}`}
            onClick={() => onNavigate(id)}
          >
            <Icon size={14} />
            {label}
          </button>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>
          Digital Twin v2.0
        </div>
        <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 2 }}>
          Modbus 127.0.0.1:5020
        </div>
      </div>
    </aside>
  );
}
