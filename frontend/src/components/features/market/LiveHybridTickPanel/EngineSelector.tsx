import React from 'react';

interface EngineSelectorProps {
  engine: string;
  setEngine: (engine: string) => void;
  isConnected: boolean;
}

export const EngineSelector: React.FC<EngineSelectorProps> = ({ engine, setEngine, isConnected }) => {
  return (
    <div className="glass-panel">
      <h2 className="gradient-text">Data Engine</h2>
      <p style={{ color: 'var(--text-secondary)', marginBottom: '1rem', fontSize: '0.9rem' }}>
        Select the underlying bridge engine for live market data.
      </p>
      
      <div className="input-group">
        <label className="input-label">Engine Provider</label>
        <select 
          className="premium-select" 
          value={engine} 
          onChange={(e) => setEngine(e.target.value)}
          disabled={isConnected}
        >
          <option value="mt5">Universal MT5 Bridge (Headless Docker)</option>
          <option value="ctrader">cTrader Open API (Native Protobuf)</option>
        </select>
      </div>
      
      <div style={{ marginTop: '1rem', padding: '1rem', backgroundColor: 'var(--bg-elevated)', borderRadius: '8px', fontSize: '0.85rem' }}>
        <strong>Current Engine Status:</strong> {engine === 'mt5' ? 'Using ZeroMQ for IPC with MT5 Docker' : 'Using TCP/TLS for direct Protobuf stream'}
      </div>
    </div>
  );
};
