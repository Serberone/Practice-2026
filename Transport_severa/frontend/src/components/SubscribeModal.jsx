import React, { useState } from 'react';
import { api } from '../api';

export default function SubscribeModal({ trip, onClose }) {
  if (!trip) return null;

  const [channel, setChannel] = useState('EMAIL');
  const [recipient, setRecipient] = useState('');
  const [loading, setLoading] = useState(false);
  const [successMsg, setSuccessMsg] = useState('');
  const [errorMsg, setErrorMsg] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!recipient.trim()) {
      setErrorMsg('Пожалуйста, укажите контакт для отправки');
      return;
    }
    setLoading(true);
    setErrorMsg('');
    setSuccessMsg('');
    try {
      const res = await api.subscribe({
        trip_id: trip.id,
        recipient: recipient.trim(),
        channel: channel,
      });
      setSuccessMsg(res.message || 'Подписка успешно оформлена!');
      setTimeout(() => {
        onClose();
      }, 2500);
    } catch (err) {
      setErrorMsg(err.message || 'Не удалось оформить подписку');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()} style={{ padding: '1.75rem', maxWidth: '480px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.75rem' }}>
          <div>
            <h3 style={{ fontSize: '1.15rem', color: '#f8fafc', fontWeight: 700 }}>
              🔔 Оповещение об изменении рейса
            </h3>
            <p style={{ fontSize: '0.8rem', color: '#94a3b8', marginTop: '0.2rem' }}>
              Рейс {trip.trip_number}: {trip.route.origin.city} → {trip.route.destination.city}
            </p>
          </div>
          <button onClick={onClose} style={{ background: 'transparent', border: 'none', color: '#94a3b8', fontSize: '1.4rem', cursor: 'pointer' }}>
            ✕
          </button>
        </div>

        {successMsg ? (
          <div style={{ background: 'rgba(16, 185, 129, 0.15)', border: '1px solid #10b981', color: '#34d399', padding: '1.25rem', borderRadius: '0.5rem', textAlign: 'center', fontSize: '0.9rem' }}>
            <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>✓</div>
            {successMsg}
          </div>
        ) : (
          <form onSubmit={handleSubmit}>
            <p style={{ fontSize: '0.85rem', color: '#cbd5e1', marginBottom: '1rem', lineHeight: 1.5 }}>
              В случае переноса, задержки из-за метели или отмены рейса мы мгновенно вышлем оперативное уведомление на ваш контакт:
            </p>

            <div style={{ marginBottom: '1rem' }}>
              <label style={{ display: 'block', fontSize: '0.8rem', color: '#94a3b8', marginBottom: '0.4rem' }}>
                Канал уведомлений:
              </label>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <button
                  type="button"
                  onClick={() => setChannel('EMAIL')}
                  className="btn"
                  style={{
                    flex: 1,
                    background: channel === 'EMAIL' ? '#0284c7' : '#0b1329',
                    color: channel === 'EMAIL' ? '#fff' : '#94a3b8',
                    border: '1px solid var(--border-color)'
                  }}
                >
                  ✉️ Электронная почта
                </button>
                <button
                  type="button"
                  onClick={() => setChannel('PUSH')}
                  className="btn"
                  style={{
                    flex: 1,
                    background: channel === 'PUSH' ? '#0284c7' : '#0b1329',
                    color: channel === 'PUSH' ? '#fff' : '#94a3b8',
                    border: '1px solid var(--border-color)'
                  }}
                >
                  📲 Push / SMS
                </button>
              </div>
            </div>

            <div style={{ marginBottom: '1.25rem' }}>
              <label style={{ display: 'block', fontSize: '0.8rem', color: '#94a3b8', marginBottom: '0.4rem' }}>
                {channel === 'EMAIL' ? 'Ваш e-mail адрес:' : 'Номер мобильного телефона:'}
              </label>
              <input
                type={channel === 'EMAIL' ? 'email' : 'tel'}
                required
                placeholder={channel === 'EMAIL' ? 'passenger@example.ru' : '+7 (912) 860-00-00'}
                value={recipient}
                onChange={(e) => setRecipient(e.target.value)}
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
                {loading ? 'Оформление...' : 'Подписаться бесплатно'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
