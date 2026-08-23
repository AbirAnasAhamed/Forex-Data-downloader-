import React, { useState } from 'react';

export const EnvironmentSettings: React.FC = () => {
  const [masterKey, setMasterKey] = useState('');
  const [dbPass, setDbPass] = useState('');

  const handleUpdate = async (key: string, value: string) => {
    if (!value) return;
    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const { apiFetch } = await import('../../../../utils/crypto');
      const response = await apiFetch(`${apiUrl}/api/config/update`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ key, value })
      });
      if (response.ok) {
        alert(`${key} updated successfully.`);
      } else {
        alert(`Failed to update ${key}.`);
      }
    } catch (e) {
      alert("Error connecting to backend API.");
    }
  };

  return (
    <div className="glass-panel">
      <h2 className="gradient-text">Environment & Security</h2>
      <p style={{ color: 'var(--text-secondary)', marginBottom: '1rem', fontSize: '0.9rem' }}>
        Manage backend .env configurations safely.
      </p>

      <div className="input-group">
        <label className="input-label">Master Encryption Key (AES-256)</label>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <input 
            type="password" 
            className="premium-input" 
            style={{ flexGrow: 1 }} 
            value={masterKey} 
            onChange={(e) => setMasterKey(e.target.value)} 
          />
          <button className="premium-button" onClick={() => handleUpdate('MASTER_ENCRYPTION_KEY', masterKey)}>Update</button>
        </div>
      </div>

      <div className="input-group">
        <label className="input-label">TimescaleDB Password</label>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <input 
            type="password" 
            className="premium-input" 
            style={{ flexGrow: 1 }} 
            value={dbPass} 
            onChange={(e) => setDbPass(e.target.value)} 
          />
          <button className="premium-button" onClick={() => handleUpdate('DB_PASSWORD', dbPass)}>Update</button>
        </div>
      </div>
    </div>
  );
};
