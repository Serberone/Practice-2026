import React, { useState } from 'react';
import { api } from '../api';

export default function LoginModal({ onClose, onSuccess }) {
  const [username, setUsername] = useState('dispatcher');
  const [password, setPassword] = useState('disp123');
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setErrorMsg('');
    try {
      const data = await api.login(username, password);
      onSuccess(data.user);
      onClose();
    } catch (err) {
      setErrorMsg(err.message || 'Ошибка авторизации');
    } finally {
      setLoading(false);
    }
  };

  const handleQuickFill = (u, p) => {
    setUsername(u);
    setPassword(p);
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()} style={{ padding: '1.75rem', maxWidth: '420px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.75rem' }}>
          <h3 style={{ fontSize: '1.15rem', color: '#f8fafc', fontWeight: 700 }}>
            🔐 Авторизация персонала
          </h3>
          <button onClick={onClose} style={{ background: 'transparent', border: 'none', color: '#94a3b8', fontSize: '1.4rem', cursor: 'pointer' }}>
            ✕
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', fontSize: '0.8rem', color: '#94a3b8', marginBottom: '0.4rem' }}>
              Имя пользователя (логин):
            </label>
            <input
              type="text"
              required
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              style={{
                width: '100%',
                background: '#0b1329',
                color: '#f8fafc',
                border: '1px solid var(--border-color)',
                borderRadius: '0.5rem',
                padding: '0.65rem 0.85rem',
                fontSize: '0.9rem',
                outline: 'none'
              }}
            />
          </div>

          <div style={{ marginBottom: '1.25rem' }}>
            <label style={{ display: 'block', fontSize: '0.8rem', color: '#94a3b8', marginBottom: '0.4rem' }}>
              Пароль:
            </label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              style={{
                width: '100%',
                background: '#0b1329',
                color: '#f8fafc',
                border: '1px solid var(--border-color)',
                borderRadius: '0.5rem',
                padding: '0.65rem 0.85rem',
                fontSize: '0.9rem',
                outline: 'none'
              }}
            />
          </div>

          {/* Demo Credentials Helper */}
          <div style={{ background: 'rgba(30, 41, 59, 0.5)', padding: '0.75rem', borderRadius: '0.375rem', border: '1px dashed var(--border-color)', marginBottom: '1.25rem', fontSize: '0.75rem', color: '#94a3b8' }}>
            <div style={{ fontWeight: 600, color: '#38bdf8', marginBottom: '0.35rem' }}>Тестовые аккаунты (кликните для быстрой подстановки):</div>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <button
                type="button"
                onClick={() => handleQuickFill('dispatcher', 'disp123')}
                style={{ background: '#0b1329', border: '1px solid var(--border-color)', color: '#fbbf24', padding: '0.2rem 0.5rem', borderRadius: '0.25rem', cursor: 'pointer', fontSize: '0.75rem' }}
              >
                Диспетчер (dispatcher)
              </button>
              <button
                type="button"
                onClick={() => handleQuickFill('admin', 'admin123')}
                style={{ background: '#0b1329', border: '1px solid var(--border-color)', color: '#c084fc', padding: '0.2rem 0.5rem', borderRadius: '0.25rem', cursor: 'pointer', fontSize: '0.75rem' }}
              >
                Администратор (admin)
              </button>
            </div>
          </div>

          {errorMsg && (
            <div style={{ background: 'rgba(239, 68, 68, 0.15)', border: '1px solid #ef4444', color: '#f87171', padding: '0.5rem 0.75rem', borderRadius: '0.375rem', fontSize: '0.8rem', marginBottom: '1rem' }}>
              {errorMsg}
            </div>
          )}

          <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end' }}>
            <button type="button" onClick={onClose} className="btn btn-secondary">
              Отмена
            </button>
            <button type="submit" disabled={loading} className="btn btn-primary">
              {loading ? 'Вход...' : 'Войти в систему'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
