import React, { useState } from 'react';

export const ExportAndMergePanel: React.FC = () => {
  const [format, setFormat] = useState('parquet');
  const [strategy, setStrategy] = useState('ffill');

  const handleExport = async () => {
    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const { apiFetch } = await import('../../../../utils/crypto');
      const response = await apiFetch(`${apiUrl}/api/data/export`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          symbol: 'EURUSD', // Mocked for now, normally would get from context
          format: format,
          strategy: strategy,
          start_time: new Date(Date.now() - 24*60*60*1000).toISOString(),
          end_time: new Date().toISOString()
        })
      });
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `export.${format}`;
        a.click();
      } else {
        alert("Export failed.");
      }
    } catch (e) {
      alert("Error connecting to export API.");
    }
  };

  return (
    <div className="glass-panel">
      <h2 className="gradient-text">Export & Merge</h2>
      <p style={{ color: 'var(--text-secondary)', marginBottom: '1rem', fontSize: '0.9rem' }}>
        Download historical and streamed data directly from TimescaleDB.
      </p>

      <div className="input-group">
        <label className="input-label">Download Format</label>
        <select className="premium-select" value={format} onChange={(e) => setFormat(e.target.value)}>
          <option value="parquet">Parquet (Highly Compressed)</option>
          <option value="feather">Feather (Fast Read/Write)</option>
          <option value="csv">CSV (Human Readable)</option>
        </select>
      </div>

      <div className="input-group">
        <label className="input-label">Merging Strategy (Tick + L2)</label>
        <select className="premium-select" value={strategy} onChange={(e) => setStrategy(e.target.value)}>
          <option value="ffill">Forward-Fill (Standard HFT)</option>
          <option value="nearest">Nearest Match (Tolerance based)</option>
          <option value="exact">Exact Match</option>
        </select>
      </div>

      <button className="premium-button primary" style={{ width: '100%', marginTop: '1rem' }} onClick={handleExport}>
        Download Data
      </button>
    </div>
  );
};
