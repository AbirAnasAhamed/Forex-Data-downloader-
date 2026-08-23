import React, { useEffect, useState, useRef } from 'react';

interface LiveTerminalWindowProps {
  symbol: string;
  isConnected: boolean;
  onConnectionDrop?: () => void;
}

export const LiveTerminalWindow: React.FC<LiveTerminalWindowProps> = ({ symbol, isConnected, onConnectionDrop }) => {
  const [logs, setLogs] = useState<string[]>([]);
  const wsRef = useRef<WebSocket | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isConnected && symbol) {
      // Create WebSocket connection
      const connectWs = async () => {
        const wsUrlBase = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';
        const { getWsToken } = await import('../../../../utils/crypto');
        const token = await getWsToken();
        const wsUrl = `${wsUrlBase}/ws/market/${symbol}?token=${token}`;
        setLogs((prev) => [...prev, `[SYSTEM] Connecting to secure stream: ${wsUrlBase}/ws/market/${symbol}...`]);
        
        wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        setLogs((prev) => [...prev, `[SYSTEM] Successfully connected to live stream for ${symbol}.`]);
      };

      wsRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'tick') {
            const time = new Date(data.timestamp).toLocaleTimeString();
            const logEntry = `[${time}] ${data.symbol} | BID: ${data.bid.toFixed(5)} | ASK: ${data.ask.toFixed(5)} | VOL: ${data.volume}`;
            setLogs((prev) => [...prev.slice(-49), logEntry]); // Keep last 50
          } else if (data.type === 'l2_snapshot') {
            const time = new Date(data.timestamp).toLocaleTimeString();
            const logEntry = `[${time}] ${data.symbol} | L2 SNAPSHOT RECEIVED | BIDS: ${data.bids.length} | ASKS: ${data.asks.length}`;
            setLogs((prev) => [...prev.slice(-49), logEntry]);
          }
        } catch (e) {
          setLogs((prev) => [...prev.slice(-49), `[RAW] ${event.data}`]);
        }
      };

      wsRef.current.onerror = () => {
        setLogs((prev) => [...prev, `[ERROR] WebSocket error occurred.`]);
        if (onConnectionDrop) onConnectionDrop();
      };

      wsRef.current.onclose = () => {
        setLogs((prev) => [...prev, `[SYSTEM] Disconnected from stream.`]);
        if (onConnectionDrop) onConnectionDrop();
      };

      };
      
      connectWs();

      return () => {
        if (wsRef.current) {
          wsRef.current.close();
        }
      };
    } else {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    }
  }, [isConnected, symbol]);

  useEffect(() => {
    if (bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs]);

  return (
    <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <h2 className="gradient-text" style={{ margin: 0 }}>Live Tick Terminal</h2>
        {isConnected && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span className="live-indicator"></span>
            <span style={{ fontSize: '0.85rem', color: 'var(--status-up)', fontWeight: 600 }}>LIVE</span>
          </div>
        )}
      </div>
      
      <div className="terminal-window" style={{ flexGrow: 1, minHeight: '300px' }}>
        <div className="terminal-header">
          <span>{symbol || 'WAITING'}</span>
          <span>{isConnected ? 'Stream Active' : 'Offline'}</span>
        </div>
        <div className="terminal-body">
          {logs.length === 0 ? (
            <div style={{ color: 'var(--text-muted)', fontStyle: 'italic' }}>
              Waiting for connection...
            </div>
          ) : (
            logs.map((log, i) => (
              <div key={i} style={{ 
                color: log.includes('ERROR') ? 'var(--status-down)' : 
                       log.includes('SYSTEM') ? 'var(--brand-primary)' : 
                       log.includes('L2') ? 'var(--brand-secondary)' : '#a9b7c6' 
              }}>
                {log}
              </div>
            ))
          )}
          <div ref={bottomRef} />
        </div>
      </div>
    </div>
  );
};
