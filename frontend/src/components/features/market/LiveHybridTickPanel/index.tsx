import React, { useState } from 'react';
import { EngineSelector } from './EngineSelector';
import { DynamicCredentials } from './DynamicCredentials';
import { LiveTerminalWindow } from './LiveTerminalWindow';
import { ExportAndMergePanel } from './ExportAndMergePanel';
import { EnvironmentSettings } from './EnvironmentSettings';

export const LiveHybridTickPanel: React.FC = () => {
  const [engine, setEngine] = useState('mt5');
  const [isConnected, setIsConnected] = useState(false);
  const [currentSymbol, setCurrentSymbol] = useState('');

  const handleConnect = async (credentials: any) => {
    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const { apiFetch } = await import('../../../../utils/crypto');
      const response = await apiFetch(`${apiUrl}/api/engine/connect`, {

        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ engine_type: engine, ...credentials }),
      });
      
      if (response.ok) {
        setIsConnected(true);
        setCurrentSymbol(credentials.symbol);
      } else {
        const error = await response.json();
        alert(`Failed to connect: ${error.detail}`);
      }
    } catch (e) {
      alert('Error connecting to backend API. Is the server running?');
    }
  };

  const handleDisconnect = async () => {
    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const { apiFetch } = await import('../../../../utils/crypto');
      await apiFetch(`${apiUrl}/api/engine/disconnect`, { method: 'POST' });
      setIsConnected(false);
      setCurrentSymbol('');
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', width: '100%' }}>
      
      <div className="grid-2">
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <EngineSelector engine={engine} setEngine={setEngine} isConnected={isConnected} />
          <DynamicCredentials 
            engine={engine} 
            onConnect={handleConnect} 
            onDisconnect={handleDisconnect}
            isConnected={isConnected} 
          />
        </div>
        
        <div>
          <LiveTerminalWindow 
            symbol={currentSymbol} 
            isConnected={isConnected} 
            onConnectionDrop={() => setIsConnected(false)} 
          />
        </div>
      </div>

      <div className="grid-2">
        <ExportAndMergePanel />
        <EnvironmentSettings />
      </div>

    </div>
  );
};
