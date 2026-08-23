import React, { useState } from 'react';

export const DownloadManager: React.FC = () => {
  const [symbol, setSymbol] = useState('EURUSD');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [isDownloading, setIsDownloading] = useState(false);

  const handleDownload = async () => {
    if (!startDate || !endDate) {
      alert("Please select start and end dates.");
      return;
    }
    
    setIsDownloading(true);
    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const { apiFetch } = await import('../../../../utils/crypto');
      const response = await apiFetch(`${apiUrl}/api/historical/download`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          symbol: symbol,
          server: 'MetaQuotes-Demo', // Hardcoded for demo, could be dynamic
          login: '123456',
          password: 'password',
          start_time: new Date(startDate).toISOString(),
          end_time: new Date(endDate).toISOString()
        })
      });
      
      const data = await response.json();
      alert(data.message || "Download started.");
    } catch (e) {
      alert("Failed to connect to backend API.");
    } finally {
      setIsDownloading(false);
    }
  };

  return (
    <div className="glass-panel">
      <h3 style={{ marginBottom: '1rem' }}>Historical Download Manager</h3>
      
      <div className="input-group">
        <label className="input-label">Symbol</label>
        <input 
          className="premium-input" 
          value={symbol} 
          onChange={(e) => setSymbol(e.target.value)} 
        />
      </div>
      
      <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem' }}>
        <div className="input-group" style={{ flex: 1 }}>
          <label className="input-label">Start Date</label>
          <input 
            type="date" 
            className="premium-input" 
            value={startDate} 
            onChange={(e) => setStartDate(e.target.value)} 
          />
        </div>
        <div className="input-group" style={{ flex: 1 }}>
          <label className="input-label">End Date</label>
          <input 
            type="date" 
            className="premium-input" 
            value={endDate} 
            onChange={(e) => setEndDate(e.target.value)} 
          />
        </div>
      </div>
      
      <button 
        className="premium-button primary" 
        style={{ width: '100%' }}
        onClick={handleDownload}
        disabled={isDownloading}
      >
        {isDownloading ? 'Fetching Chunks...' : 'Download Historical Data (RAM Safe)'}
      </button>
    </div>
  );
};
