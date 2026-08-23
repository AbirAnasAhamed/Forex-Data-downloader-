import React, { useState } from 'react';

export const AITrainingMonitor: React.FC = () => {
  const [isTraining, setIsTraining] = useState(false);
  const [logs, setLogs] = useState<string[]>([]);

  const handleTrain = async () => {
    setIsTraining(true);
    setLogs((prev) => [...prev, "[SYSTEM] Initializing PyTorch Data Lake Loader..."]);
    
    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const { apiFetch } = await import('../../../../utils/crypto');
      const response = await apiFetch(`${apiUrl}/api/historical/train_ai`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ symbol: 'EURUSD', timeframe: '1m' })
      });
      
      const data = await response.json();
      setLogs((prev) => [...prev, `[API] ${data.message}`]);
      
      // Mocking training stream
      setTimeout(() => setLogs((prev) => [...prev, "[PyTorch] Epoch 1/100 - loss: 0.0432"]), 1000);
      setTimeout(() => setLogs((prev) => [...prev, "[PyTorch] Epoch 2/100 - loss: 0.0381"]), 2000);
      setTimeout(() => {
        setLogs((prev) => [...prev, "[SYSTEM] Training complete. Model saved."]);
        setIsTraining(false);
      }, 3000);
      
    } catch (e) {
      setLogs((prev) => [...prev, "[ERROR] Failed to start training."]);
      setIsTraining(false);
    }
  };

  return (
    <div className="glass-panel" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <h3>AI Training Monitor</h3>
        <button 
          className="premium-button" 
          onClick={handleTrain}
          disabled={isTraining}
        >
          {isTraining ? 'Training...' : 'Start AI Training'}
        </button>
      </div>
      
      <div 
        style={{ 
          flex: 1, 
          backgroundColor: '#00000088', 
          borderRadius: '8px', 
          padding: '1rem',
          fontFamily: 'monospace',
          color: '#0f0',
          overflowY: 'auto',
          minHeight: '200px'
        }}
      >
        {logs.length === 0 ? (
          <span style={{ color: '#555' }}>Waiting to start PyTorch...</span>
        ) : (
          logs.map((log, i) => (
            <div key={i} style={{ marginBottom: '0.2rem' }}>{log}</div>
          ))
        )}
      </div>
    </div>
  );
};
