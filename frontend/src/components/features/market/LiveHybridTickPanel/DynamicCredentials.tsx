import React, { useState, useEffect } from 'react';

interface DynamicCredentialsProps {
  engine: string;
  onConnect: (credentials: any) => void;
  onDisconnect: () => void;
  isConnected: boolean;
}

interface Broker {
  id: string;
  name: string;
  default_server: string;
}

// Module-level cache to prevent redundant API calls
let cachedBrokersDB: Record<string, Broker[]> | null = null;

export const DynamicCredentials: React.FC<DynamicCredentialsProps> = ({ engine, onConnect, onDisconnect, isConnected }) => {
  const [symbol, setSymbol] = useState('EURUSD');
  const [server, setServer] = useState('');
  const [login, setLogin] = useState('');
  const [password, setPassword] = useState('');
  const [clientId, setClientId] = useState('');
  const [secret, setSecret] = useState('');
  const [token, setToken] = useState('');
  const [accountId, setAccountId] = useState('');
  
  const [brokersDB, setBrokersDB] = useState<Record<string, Broker[]>>({});
  const [selectedBrokerId, setSelectedBrokerId] = useState<string>('');

  useEffect(() => {
    if (cachedBrokersDB) {
      setBrokersDB(cachedBrokersDB);
    } else {
      const fetchBrokers = async () => {
        try {
          const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
          const { apiFetch } = await import('../../../../utils/crypto');
          const res = await apiFetch(`${apiUrl}/api/brokers/list`);
          if (res.ok) {
            const data = await res.json();
            cachedBrokersDB = data;
            setBrokersDB(data);
          }
        } catch (e) {
          console.error("Failed to fetch brokers", e);
        }
      };
      fetchBrokers();
    }
  }, []);

  // When engine changes, reset broker selection and server
  useEffect(() => {
    setSelectedBrokerId('');
    if (engine === 'mt5') {
      setServer('');
    }
  }, [engine]);

  const handleBrokerChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const val = e.target.value;
    setSelectedBrokerId(val);
    
    if (val && val !== 'custom') {
      const brokerList = brokersDB[engine] || [];
      const broker = brokerList.find(b => b.id === val);
      if (broker && engine === 'mt5') {
        setServer(broker.default_server);
      }
    } else {
      if (engine === 'mt5') {
        setServer('');
      }
    }
  };

  const handleConnect = () => {
    if (!symbol.trim()) {
      alert("Symbol is required!");
      return;
    }
    if (engine === 'mt5') {
      if (!login || !password || !server) {
        alert("Server, Login ID, and Password are required for MT5!");
        return;
      }
      if (isNaN(Number(login))) {
        alert("MT5 Login ID must be a numeric value!");
        return;
      }
      onConnect({ symbol, server, login, password });
    } else {
      if (!clientId || !secret || !token) {
        alert("Client ID, Secret, and Token are required for cTrader!");
        return;
      }
      onConnect({ symbol, client_id: clientId, secret, token, account_id: accountId });
    }
  };

  const currentBrokers = brokersDB[engine] || [];

  return (
    <div className="glass-panel">
      <h2 className="gradient-text">Authentication & Symbol</h2>
      <p style={{ color: 'var(--text-secondary)', marginBottom: '1rem', fontSize: '0.9rem' }}>
        Provide your credentials. They are never hardcoded and will be encrypted in the backend.
      </p>

      <div className="input-group">
        <label className="input-label">Symbol to stream (e.g. EURUSD, XAUUSD)</label>
        <input 
          type="text" 
          className="premium-input" 
          value={symbol} 
          onChange={(e) => setSymbol(e.target.value)}
          disabled={isConnected}
        />
      </div>
      
      <div className="input-group">
        <label className="input-label">Select Broker</label>
        <select 
          className="premium-input" 
          value={selectedBrokerId} 
          onChange={handleBrokerChange} 
          disabled={isConnected}
          style={{ appearance: 'none', backgroundColor: 'rgba(255,255,255,0.05)', color: 'white' }}
        >
          <option value="" style={{ color: 'black' }}>-- Select a Broker --</option>
          {currentBrokers.map(b => (
            <option key={b.id} value={b.id} style={{ color: 'black' }}>{b.name}</option>
          ))}
          <option value="custom" style={{ color: 'black' }}>Other / Custom Broker</option>
        </select>
      </div>

      {engine === 'mt5' ? (
        <>
          <div className="input-group">
            <label className="input-label">Broker Server Name</label>
            <input type="text" className="premium-input" value={server} onChange={(e) => setServer(e.target.value)} disabled={isConnected} placeholder="e.g. MetaQuotes-Demo"/>
          </div>
          <div className="input-group">
            <label className="input-label">Login ID</label>
            <input type="text" className="premium-input" value={login} onChange={(e) => setLogin(e.target.value)} disabled={isConnected}/>
          </div>
          <div className="input-group">
            <label className="input-label">Password</label>
            <input type="password" className="premium-input" value={password} onChange={(e) => setPassword(e.target.value)} disabled={isConnected}/>
          </div>
        </>
      ) : (
        <>
          <div className="input-group">
            <label className="input-label">Client ID</label>
            <input type="text" className="premium-input" value={clientId} onChange={(e) => setClientId(e.target.value)} disabled={isConnected}/>
          </div>
          <div className="input-group">
            <label className="input-label">Secret</label>
            <input type="password" className="premium-input" value={secret} onChange={(e) => setSecret(e.target.value)} disabled={isConnected}/>
          </div>
          <div className="input-group">
            <label className="input-label">Access Token</label>
            <input type="password" className="premium-input" value={token} onChange={(e) => setToken(e.target.value)} disabled={isConnected}/>
          </div>
          <div className="input-group">
            <label className="input-label">cTrader Account ID</label>
            <input type="text" className="premium-input" value={accountId} onChange={(e) => setAccountId(e.target.value)} disabled={isConnected}/>
          </div>
        </>
      )}

      <div style={{ marginTop: '1.5rem', display: 'flex', gap: '1rem' }}>
        {!isConnected ? (
          <button className="premium-button primary" onClick={handleConnect} style={{ flex: 1 }}>
            Connect & Stream
          </button>
        ) : (
          <button className="premium-button danger" onClick={onDisconnect} style={{ flex: 1 }}>
            Disconnect Engine
          </button>
        )}
      </div>
    </div>
  );
};
