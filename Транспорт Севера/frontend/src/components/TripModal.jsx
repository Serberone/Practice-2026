import React from 'react';

export default function TripModal({ trip, onClose, onSubscribe }) {
  if (!trip) return null;

  const formatDateTime = (isoString) => {
    if (!isoString) return '—';
    const d = new Date(isoString);
    return `${d.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })} (${d.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric' })})`;
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()} style={{ padding: '1.75rem' }}>
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', borderBottom: '1px solid var(--border-color)', paddingBottom: '1rem', marginBottom: '1.25rem' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <span className="font-mono" style={{ fontSize: '1.5rem', fontWeight: 800, color: '#38bdf8' }}>
                {trip.trip_number}
              </span>
              <span className="badge badge-scheduled" style={{ textTransform: 'uppercase' }}>
                {trip.transport_type === 'PLANE' ? 'Авиарейс' : 'Междугородний автобус'}
              </span>
            </div>
            <div style={{ fontSize: '1.1rem', fontWeight: 600, color: '#f8fafc', marginTop: '0.25rem' }}>
              {trip.route.origin.city} → {trip.route.destination.city}
            </div>
          </div>
          <button onClick={onClose} style={{ background: 'transparent', border: 'none', color: '#94a3b8', fontSize: '1.5rem', cursor: 'pointer' }}>
            ✕
          </button>
        </div>

        {/* Status Banner */}
        <div style={{
          background: trip.status === 'DELAYED' ? 'rgba(245, 158, 11, 0.15)' : trip.status === 'CANCELLED' ? 'rgba(239, 68, 68, 0.15)' : 'rgba(16, 185, 129, 0.15)',
          border: `1px solid ${trip.status === 'DELAYED' ? '#f59e0b' : trip.status === 'CANCELLED' ? '#ef4444' : '#10b981'}`,
          borderRadius: '0.5rem',
          padding: '0.875rem',
          marginBottom: '1.25rem'
        }}>
          <div style={{ fontWeight: 700, fontSize: '0.95rem', color: trip.status === 'DELAYED' ? '#fbbf24' : trip.status === 'CANCELLED' ? '#f87171' : '#34d399' }}>
            Статус: {trip.status === 'SCHEDULED' ? 'По расписанию' : trip.status === 'DELAYED' ? 'Задержан' : trip.status === 'CANCELLED' ? 'Отменён' : trip.status === 'BOARDING' ? 'Идёт посадка' : trip.status}
          </div>
          {trip.weather_factor?.has_impact && (
            <div style={{ fontSize: '0.85rem', color: '#cbd5e1', marginTop: '0.25rem' }}>
              ❄️ <strong>Метеофактор:</strong> {trip.weather_factor.phenomenon}
            </div>
          )}
        </div>

        {/* Route & Times Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', background: '#0b1329', padding: '1rem', borderRadius: '0.5rem', border: '1px solid var(--border-color)', marginBottom: '1.25rem' }}>
          <div>
            <div style={{ fontSize: '0.75rem', color: '#94a3b8', textTransform: 'uppercase' }}>Пункт отправления</div>
            <div style={{ fontWeight: 600, color: '#f8fafc', fontSize: '0.95rem' }}>{trip.route.origin.name}</div>
            <div style={{ fontSize: '0.8rem', color: '#38bdf8', marginTop: '0.25rem' }}>
              План: {formatDateTime(trip.schedule.departure_planned)}
            </div>
            {trip.schedule.departure_estimated && (
              <div style={{ fontSize: '0.8rem', color: '#f59e0b', fontWeight: 600 }}>
                Расчётное: {formatDateTime(trip.schedule.departure_estimated)}
              </div>
            )}
          </div>

          <div>
            <div style={{ fontSize: '0.75rem', color: '#94a3b8', textTransform: 'uppercase' }}>Пункт назначения</div>
            <div style={{ fontWeight: 600, color: '#f8fafc', fontSize: '0.95rem' }}>{trip.route.destination.name}</div>
            <div style={{ fontSize: '0.8rem', color: '#38bdf8', marginTop: '0.25rem' }}>
              План: {formatDateTime(trip.schedule.arrival_planned)}
            </div>
            {trip.schedule.arrival_estimated && (
              <div style={{ fontSize: '0.8rem', color: '#f59e0b', fontWeight: 600 }}>
                Расчётное: {formatDateTime(trip.schedule.arrival_estimated)}
              </div>
            )}
          </div>
        </div>

        {/* Carrier & Gate */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#111e33', padding: '0.75rem 1rem', borderRadius: '0.5rem', border: '1px solid var(--border-color)', marginBottom: '1.5rem' }}>
          <div>
            <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Перевозчик: </span>
            <strong style={{ color: '#f8fafc', fontSize: '0.85rem' }}>{trip.carrier.name}</strong>
            {trip.carrier.phone && <div style={{ fontSize: '0.75rem', color: '#64748b' }}>тел. {trip.carrier.phone}</div>}
          </div>
          <div>
            <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Сектор / Выход: </span>
            <strong className="font-mono" style={{ color: '#38bdf8', fontSize: '0.95rem' }}>{trip.gate_or_platform || 'Не назначен'}</strong>
          </div>
        </div>

        {/* Action Buttons */}
        <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end' }}>
          <button onClick={onClose} className="btn btn-secondary">
            Закрыть
          </button>
          <button
            onClick={() => {
              onClose();
              onSubscribe(trip);
            }}
            className="btn btn-primary"
          >
            🔔 Получать оповещения по этому рейсу
          </button>
        </div>
      </div>
    </div>
  );
}
