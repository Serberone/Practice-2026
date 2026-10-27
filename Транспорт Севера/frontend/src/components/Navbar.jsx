import React, { useState, useEffect } from 'react';

export default function Navbar({ activeTab, setActiveTab, currentUser, onOpenLogin, onLogout }) {
  const [currentTime, setCurrentTime] = useState('');

  useEffect(() => {
    const updateClock = () => {
      const now = new Date();
      setCurrentTime(now.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit', second: '2-digit' }));
    };
    updateClock();
    const interval = setInterval(updateClock, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header style={{ background: 'var(--bg-header)', borderBottom: '1px solid var(--border-color)', position: 'relative', zIndex: 20 }}>
      <div className="container" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', minHeight: '4.5rem', paddingTop: '0.75rem', paddingBottom: '0.75rem', flexWrap: 'wrap', gap: '0.75rem 1rem' }}>
        {/* Brand */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.875rem', cursor: 'pointer', flexShrink: 0 }} onClick={() => setActiveTab('board')}>
          <div style={{ background: 'linear-gradient(135deg, #0284c7, #38bdf8)', width: '2.5rem', height: '2.5rem', borderRadius: '0.625rem', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 4px 12px rgba(56, 189, 248, 0.25)' }}>
            <span style={{ fontSize: '1.25rem' }}>❄️</span>
          </div>
          <div>
            <div style={{ fontWeight: 700, fontSize: '1.15rem', letterSpacing: '-0.02em', color: '#f8fafc' }}>
              Транспорт Севера
            </div>
            <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
              Онлайн-табло Республики Коми
            </div>
          </div>
        </div>

        {/* Live Clock & Status */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flexShrink: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: 'rgba(15, 23, 42, 0.6)', padding: '0.35rem 0.85rem', borderRadius: '9999px', border: '1px solid var(--border-color)' }}>
            <span style={{ width: '0.5rem', height: '0.5rem', borderRadius: '50%', background: '#10b981', display: 'inline-block' }} className="animate-pulse-slow"></span>
            <span style={{ fontSize: '0.75rem', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Сыктывкар (МСК)</span>
            <span className="font-mono" style={{ fontSize: '0.9rem', fontWeight: 700, color: '#38bdf8' }}>{currentTime}</span>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
          <button
            onClick={() => setActiveTab('board')}
            className="btn"
            style={{
              background: activeTab === 'board' ? 'rgba(56, 189, 248, 0.15)' : 'transparent',
              color: activeTab === 'board' ? '#38bdf8' : '#94a3b8',
              borderColor: activeTab === 'board' ? '#0284c7' : 'transparent',
            }}
          >
            📋 Онлайн-табло
          </button>

          {currentUser?.role === 'DISPATCHER' || currentUser?.role === 'ADMIN' ? (
            <button
              onClick={() => setActiveTab('dispatcher')}
              className="btn"
              style={{
                background: activeTab === 'dispatcher' ? 'rgba(245, 158, 11, 0.15)' : 'transparent',
                color: activeTab === 'dispatcher' ? '#fbbf24' : '#94a3b8',
                borderColor: activeTab === 'dispatcher' ? '#d97706' : 'transparent',
              }}
            >
              🎧 Диспетчер
            </button>
          ) : null}

          {currentUser?.role === 'ADMIN' ? (
            <button
              onClick={() => setActiveTab('admin')}
              className="btn"
              style={{
                background: activeTab === 'admin' ? 'rgba(168, 85, 247, 0.15)' : 'transparent',
                color: activeTab === 'admin' ? '#c084fc' : '#94a3b8',
                borderColor: activeTab === 'admin' ? '#9333ea' : 'transparent',
              }}
            >
              ⚙️ Администратор
            </button>
          ) : null}

          {/* User / Auth */}
          {currentUser ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginLeft: '0.5rem' }}>
              <span style={{ fontSize: '0.825rem', color: '#cbd5e1' }}>
                👤 {currentUser.full_name || currentUser.username} ({currentUser.role})
              </span>
              <button onClick={onLogout} className="btn btn-secondary" style={{ padding: '0.35rem 0.75rem', fontSize: '0.775rem' }}>
                Выйти
              </button>
            </div>
          ) : (
            <button onClick={onOpenLogin} className="btn btn-primary" style={{ marginLeft: '0.5rem', padding: '0.45rem 1rem' }}>
              Вход для персонала
            </button>
          )}
        </nav>
      </div>
    </header>
  );
}
