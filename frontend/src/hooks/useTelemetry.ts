import { useState, useEffect, useRef, useCallback } from 'react';
import type { TelemetryFrame } from '../types';

interface WsMessage {
  type: string;
  data: TelemetryFrame;
}

interface UseTelemetryReturn {
  latest: TelemetryFrame | null;
  history: TelemetryFrame[];
  connected: boolean;
  paused: boolean;
  setPaused: (p: boolean) => void;
}

const MAX_HISTORY = 600; // 60 s at 10 Hz

export function useTelemetry(): UseTelemetryReturn {
  const [latest, setLatest] = useState<TelemetryFrame | null>(null);
  const [history, setHistory] = useState<TelemetryFrame[]>([]);
  const [connected, setConnected] = useState(false);
  const [paused, setPaused] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const pausedRef = useRef(false);

  useEffect(() => { pausedRef.current = paused; }, [paused]);

  const timeoutRef = useRef<NodeJS.Timeout | undefined>(undefined);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN || wsRef.current?.readyState === WebSocket.CONNECTING) {
      return;
    }

    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const ws = new WebSocket(`${protocol}://${window.location.host}/ws/telemetry`);

    ws.onopen = () => setConnected(true);

    ws.onmessage = (ev) => {
      if (pausedRef.current) return;
      try {
        const msg: WsMessage = JSON.parse(ev.data);
        if (msg.type === 'telemetry' && msg.data) {
          setLatest(msg.data);
          setHistory((prev) => {
            const next = [...prev, msg.data];
            return next.length > MAX_HISTORY ? next.slice(next.length - MAX_HISTORY) : next;
          });
        }
      } catch {}
    };

    ws.onclose = () => {
      setConnected(false);
      // Reconnect after 2 s
      timeoutRef.current = setTimeout(connect, 2000);
    };

    ws.onerror = () => ws.close();
    wsRef.current = ws;
  }, []);

  useEffect(() => {
    connect();
    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      if (wsRef.current) {
        wsRef.current.onclose = null; // Prevent reconnect on unmount
        wsRef.current.close();
      }
    };
  }, [connect]);

  return { latest, history, connected, paused, setPaused };
}
