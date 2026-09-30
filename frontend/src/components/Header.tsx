import React from 'react';
import type { TelemetryFrame } from '../types';

interface Props {
  connected: boolean;
  latest: TelemetryFrame | null;
}

function Dot({ color, pulse }: { color: string; pulse?: boolean }) {
  return (
    <span
      className={`status-dot ${color}${pulse ? ' pulse' : ''}`}
    />
  );
}

export default function Header({ connected, latest }: Props) {
  const modbusOk = connected;
  const detectionOk = connected;
  const hasAttack = Boolean(latest?.active_attack);

  return (
    <header className="header">
      <div className="header-left">
        <span className="header-title">TwinGuard-OT</span>
        <span style={{ color: 'var(--border)', fontSize: 12 }}>|</span>
        <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
          Industrial Cybersecurity Digital Twin
        </span>
      </div>

      <div className="header-right">
        {hasAttack && (
          <span className="badge red" style={{ fontSize: 9 }}>
            ⚡ ATTACK ACTIVE: {latest?.active_attack?.replace('_', ' ').toUpperCase()}
          </span>
        )}

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

        <span className="status-pill">
          <Dot color={connected ? 'blue' : 'red'} />
          API
        </span>

        <span style={{ fontSize: 11, color: 'var(--text-muted)', fontVariantNumeric: 'tabular-nums' }}>
          {new Date().toLocaleTimeString()}
        </span>
      </div>
    </header>
  );
}
