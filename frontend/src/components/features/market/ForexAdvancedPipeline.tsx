import React, { useState } from 'react';
import { LiveHybridTickPanel } from './LiveHybridTickPanel';
import { HistoricalDataPanel } from './HistoricalDataPanel';

export const ForexAdvancedPipeline: React.FC = () => {
  const [activeTab, setActiveTab] = useState('hybrid_live_tick');

  return (
    <div style={{ width: '100%' }}>
      <header style={{ marginBottom: '2rem', textAlign: 'center' }}>
        <h1 className="gradient-text" style={{ fontSize: '2.5rem', marginBottom: '0.5rem' }}>Forex Training Studio</h1>
        <p style={{ color: 'var(--text-secondary)' }}>Advanced L2 Snapshot & Tick Data Pipeline</p>
      </header>

      <div style={{ display: 'flex', gap: '1rem', marginBottom: '2rem', justifyContent: 'center' }}>
        <button 
          className={`premium-button ${activeTab === 'hybrid_live_tick' ? 'primary' : ''}`}
          onClick={() => setActiveTab('hybrid_live_tick')}
        >
          Hybrid Live Tick
        </button>
        <button 
          className={`premium-button ${activeTab === 'historical' ? 'primary' : ''}`}
          onClick={() => setActiveTab('historical')}
        >
          Historical Data
        </button>
      </div>

      <main>
        {activeTab === 'hybrid_live_tick' && <LiveHybridTickPanel />}
        {activeTab === 'historical' && <HistoricalDataPanel />}
      </main>
    </div>
  );
};
