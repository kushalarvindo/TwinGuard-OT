import React, { useEffect, useState } from 'react';
import { api } from '../api';
import type { SystemStatus } from '../types';
import { CheckCircle2, XCircle } from 'lucide-react';

export default function SystemPage() {
  const [status, setStatus] = useState<SystemStatus | null>(null);

  useEffect(() => {
    const load = () => api.system.status().then(r => setStatus(r as SystemStatus)).catch(() => {});
    load();
    const id = setInterval(load, 5000);
    return () => clearInterval(id);
  }, []);

  const components = status ? [
    { name: 'Overall System', key: 'overall', okValues: ['OPERATIONAL'] },
    { name: 'Digital Twin Process', key: 'digital_twin', okValues: ['ONLINE'] },
    { name: 'Virtual PLC', key: 'virtual_plc', okValues: ['ONLINE'] },
    { name: 'Modbus TCP Server', key: 'modbus_server', okValues: ['ONLINE'] },
    { name: 'Telemetry Collector', key: 'telemetry_collector', okValues: ['ONLINE'] },
    { name: 'Detection Engine', key: 'detection_engine', okValues: ['ACTIVE'] },
    { name: 'ML Isolation Forest', key: 'ml_model', okValues: ['READY'] },
    { name: 'SQLite Database', key: 'database', okValues: ['ONLINE'] },
  ] : [];

  return (
    <div>
      <div className="page-header">
        <div className="page-title">System Health</div>
        <div className="page-sub">Subsystem connectivity and operational readiness</div>
      </div>

      <div className="panel" style={{ maxWidth: 600 }}>
        <div className="panel-header">
          <span className="panel-title">Subsystem Status</span>
        </div>
        <div className="panel-body no-pad">
          {!status ? (
            <div className="loading-state">Checking subsystems...</div>
          ) : (
            components.map((c, i) => {
              const val = status[c.key as keyof SystemStatus] as string;
              const ok = c.okValues.includes(val);
              return (
                <div key={c.key} style={{
                  padding: '12px 16px',
                  borderBottom: i < components.length - 1 ? '1px solid var(--border-light)' : 'none',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  background: c.key === 'overall' ? 'var(--bg-raised)' : 'transparent'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    {ok ? <CheckCircle2 size={16} color="var(--color-green)" /> : <XCircle size={16} color="var(--color-red)" />}
                    <span style={{ fontSize: 13, fontWeight: c.key === 'overall' ? 600 : 500, color: 'var(--text-primary)' }}>
                      {c.name}
                    </span>
                  </div>
                  <span className={`badge ${ok ? 'green' : 'amber'}`}>{val}</span>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}
