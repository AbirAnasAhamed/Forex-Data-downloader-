import React from 'react';
import { DownloadManager } from './DownloadManager';
import { AITrainingMonitor } from './AITrainingMonitor';

export const HistoricalDataPanel: React.FC = () => {
  return (
    <div style={{ display: 'grid', gap: '2rem', gridTemplateColumns: '1fr 1fr' }}>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
        <div className="glass-panel">
          <h2 className="gradient-text">Hedge Fund Architecture</h2>
          <p style={{ color: 'var(--text-secondary)' }}>
            Phase 7 encompasses MT5 Chunking, Polars Feature Engineering, and PyTorch Memory-Mapped Data Lakes.
          </p>
        </div>
        <DownloadManager />
      </div>
      <div>
        <AITrainingMonitor />
      </div>
    </div>
  );
};
