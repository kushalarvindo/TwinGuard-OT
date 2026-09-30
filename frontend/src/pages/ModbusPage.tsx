import React, { useEffect, useState } from 'react';
import { api } from '../api';

function fmtTime(ts: number) {
  return new Date(ts * 1000).toLocaleTimeString(undefined, { hour12: false });
}

export default function ModbusPage() {
  const [status, setStatus] = useState<Record<string, unknown> | null>(null);
  const [registers, setRegisters] = useState<Record<string, unknown>[]>([]);
  const [events, setEvents] = useState<Record<string, unknown>[]>([]);

  useEffect(() => {
    const load = async () => {
      try {
        const [s, r, e] = await Promise.all([
          api.modbus.status(),
          api.modbus.registers(),
          api.modbus.events(80),
        ]);
        setStatus(s); setRegisters(r); setEvents(e);
      } catch {}
    };
    load();
    const id = setInterval(load, 2000);
    return () => clearInterval(id);
  }, []);

  const isOnline = status?.is_running as boolean;

  return (
    <div>
      <div className="page-header">
        <div className="page-title">Modbus Monitor</div>
        <div className="page-sub">Modbus TCP register state and transaction audit log</div>
      </div>

      {/* Connection status */}
      <div className="panel" style={{ marginBottom: 14 }}>
        <div className="panel-body compact">
          <div style={{ display: 'flex', alignItems: 'center', gap: 20 }}>
            <div>
              <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 2 }}>Endpoint</div>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 13, color: 'var(--text-primary)' }}>
                {String(status?.host ?? '127.0.0.1')}:{String(status?.port ?? '5020')}
              </div>
            </div>
            <div>
              <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 2 }}>Status</div>
              <span className={`badge ${isOnline ? 'green' : 'red'}`}>{isOnline ? 'CONNECTED' : 'OFFLINE'}</span>
            </div>
            <div>
              <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 2 }}>Transactions</div>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 13, color: 'var(--text-primary)' }}>
                {String(status?.transaction_count ?? 0)}
              </div>
            </div>
            <div>
              <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 2 }}>Request Rate</div>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 13, color: (Number(status?.request_rate) > 30) ? 'var(--color-amber)' : 'var(--text-primary)' }}>
                {Number(status?.request_rate ?? 0).toFixed(1)} r/s
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="grid-2-1" style={{ gap: 12 }}>
        {/* Register map */}
        <div className="panel">
          <div className="panel-header">
            <span className="panel-title">Holding Registers (40001 – 40012)</span>
          </div>
          <div className="panel-body no-pad">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Address</th>
                  <th>Name</th>
                  <th>Value</th>
                  <th>Unit</th>
                  <th>R/W</th>
                </tr>
              </thead>
              <tbody>
                {registers.map((r, i) => (
                  <tr key={i}>
                    <td className="mono" style={{ color: 'var(--text-muted)' }}>{String(r.address)}</td>
                    <td style={{ fontSize: 11, color: 'var(--text-primary)', fontWeight: 500 }}>{String(r.name)}</td>
                    <td className="mono" style={{ color: 'var(--color-teal)' }}>{Number(r.value).toFixed(1)}</td>
                    <td style={{ color: 'var(--text-muted)' }}>{String(r.unit)}</td>
                    <td>
                      <span className={`badge ${r.rw === 'RW' ? 'amber' : 'gray'}`}>{String(r.rw)}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Transaction log */}
        <div className="panel">
          <div className="panel-header">
            <span className="panel-title">Transaction Log</span>
            <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>Last 80</span>
          </div>
          <div className="panel-body no-pad" style={{ maxHeight: 420, overflowY: 'auto' }}>
            {events.length === 0 ? (
              <div className="empty-state">No Modbus transactions recorded yet</div>
            ) : (
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Time</th>
                    <th>Register</th>
                    <th>Op</th>
                    <th>Value</th>
                  </tr>
                </thead>
                <tbody>
                  {events.map((e, i) => (
                    <tr key={i}>
                      <td className="mono" style={{ color: 'var(--text-muted)', fontSize: 10 }}>
                        {fmtTime(Number(e.timestamp))}
                      </td>
                      <td className="mono">{String(e.register_address)}</td>
                      <td>
                        <span className={`badge ${e.is_write ? 'red' : 'blue'}`}>
                          {e.is_write ? 'WRITE' : 'READ'}
                        </span>
                      </td>
                      <td className="mono" style={{ color: 'var(--color-teal)' }}>{String(e.value)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
