import React, { useState, useEffect } from 'react';
import { api } from '../api';

export default function Board({ onSelectTrip, onSubscribeTrip }) {
  const [trips, setTrips] = useState([]);
  const [loading, setLoading] = useState(true);
  const [transportType, setTransportType] = useState('PLANE'); // PLANE or BUS
  const [direction, setDirection] = useState('DEPARTURE'); // DEPARTURE or ARRIVAL
  const [cityFilter, setCityFilter] = useState('');
  const [searchQuery, setSearchQuery] = useState('');

  const loadTrips = async () => {
    try {
      setLoading(true);
      const params = {
        transport_type: transportType,
        direction: direction,
      };
      if (cityFilter) params.city = cityFilter;
      if (searchQuery) params.search = searchQuery;
      const data = await api.getTrips(params);
      setTrips(data);
    } catch (e) {
      console.error('Error fetching trips', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTrips();
    const interval = setInterval(loadTrips, 30000); // 30 sec auto-refresh
    return () => clearInterval(interval);
  }, [transportType, direction, cityFilter, searchQuery]);

  const formatTime = (isoString) => {
    if (!isoString) return '—';
    const d = new Date(isoString);
    return d.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
  };

  const formatDate = (isoString) => {
    if (!isoString) return '';
    const d = new Date(isoString);
    return d.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit' });
  };

  const getStatusBadge = (status, weatherFactor) => {
    switch (status) {
      case 'BOARDING':
        return <span className="badge badge-boarding">● Посадка</span>;
      case 'DELAYED':
        return (
          <span className="badge badge-delayed" title={weatherFactor?.phenomenon || 'Рейс задержан'}>
            ⚠️ Задержан
          </span>
        );
      case 'CANCELLED':
        return (
          <span className="badge badge-cancelled" title={weatherFactor?.phenomenon || 'Рейс отменён'}>
            ✕ Отменён
          </span>
        );
      case 'ARRIVED':
        return <span className="badge badge-arrived">✓ Прибыл</span>;
      case 'DEPARTED':
        return <span className="badge badge-arrived">✓ Отправлен</span>;
      case 'SCHEDULED':
      default:
        return <span className="badge badge-scheduled">По расписанию</span>;
    }
  };

  return (
    <div className="container" style={{ padding: '2rem 1rem' }}>
      {/* Top Filter Controls */}
      <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: '0.75rem', padding: '1.25rem', marginBottom: '1.5rem', boxShadow: '0 4px 20px rgba(0,0,0,0.2)' }}>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '1rem', alignItems: 'center', justifyContent: 'space-between' }}>
          
          {/* Mode Switchers */}
          <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
            {/* Transport Type */}
            <div style={{ display: 'flex', background: '#0b1329', padding: '0.25rem', borderRadius: '0.5rem', border: '1px solid var(--border-color)' }}>
              <button
                onClick={() => setTransportType('PLANE')}
                className="btn"
                style={{
                  background: transportType === 'PLANE' ? '#0284c7' : 'transparent',
                  color: transportType === 'PLANE' ? '#ffffff' : '#94a3b8',
                  padding: '0.4rem 1rem',
                  fontSize: '0.85rem'
                }}
              >
                ✈️ Авиарейсы
              </button>
              <button
                onClick={() => setTransportType('BUS')}
                className="btn"
                style={{
                  background: transportType === 'BUS' ? '#0284c7' : 'transparent',
                  color: transportType === 'BUS' ? '#ffffff' : '#94a3b8',
                  padding: '0.4rem 1rem',
                  fontSize: '0.85rem'
                }}
              >
                🚌 Автобусы
              </button>
            </div>

            {/* Direction */}
            <div style={{ display: 'flex', background: '#0b1329', padding: '0.25rem', borderRadius: '0.5rem', border: '1px solid var(--border-color)' }}>
              <button
                onClick={() => setDirection('DEPARTURE')}
                className="btn"
                style={{
                  background: direction === 'DEPARTURE' ? '#1e293b' : 'transparent',
                  color: direction === 'DEPARTURE' ? '#38bdf8' : '#94a3b8',
                  padding: '0.4rem 1rem',
                  fontSize: '0.85rem'
                }}
              >
                🛫 Вылет / Отправление
              </button>
              <button
                onClick={() => setDirection('ARRIVAL')}
                className="btn"
                style={{
                  background: direction === 'ARRIVAL' ? '#1e293b' : 'transparent',
                  color: direction === 'ARRIVAL' ? '#38bdf8' : '#94a3b8',
                  padding: '0.4rem 1rem',
                  fontSize: '0.85rem'
                }}
              >
                🛬 Прилёт / Прибытие
              </button>
            </div>
          </div>

          {/* City & Search */}
          <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap', alignItems: 'center' }}>
            <select
              value={cityFilter}
              onChange={(e) => setCityFilter(e.target.value)}
              style={{
                background: '#0b1329',
                color: '#f8fafc',
                border: '1px solid var(--border-color)',
                borderRadius: '0.5rem',
                padding: '0.5rem 0.85rem',
                fontSize: '0.85rem',
                outline: 'none',
                cursor: 'pointer'
              }}
            >
              <option value="">Все города Республики Коми</option>
              <option value="Сыктывкар">Сыктывкар</option>
              <option value="Усинск">Усинск</option>
              <option value="Ухта">Ухта</option>
              <option value="Печора">Печора</option>
            </select>

            <input
              type="text"
              placeholder="Поиск рейса или маршрута..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{
                background: '#0b1329',
                color: '#f8fafc',
                border: '1px solid var(--border-color)',
                borderRadius: '0.5rem',
                padding: '0.5rem 0.85rem',
                fontSize: '0.85rem',
                outline: 'none',
                minWidth: '220px'
              }}
            />

            <button onClick={loadTrips} className="btn btn-secondary" title="Обновить сейчас">
              🔄
            </button>
          </div>
        </div>
      </div>

      {/* Scoreboard Table / Grid */}
      <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: '0.75rem', overflow: 'hidden', boxShadow: '0 10px 30px rgba(0,0,0,0.3)' }}>
        <div style={{ padding: '1rem 1.25rem', borderBottom: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'rgba(11, 19, 41, 0.5)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <span style={{ fontSize: '1.25rem' }}>{transportType === 'PLANE' ? '✈️' : '🚌'}</span>
            <span style={{ fontWeight: 600, fontSize: '1rem', color: '#f8fafc' }}>
              {transportType === 'PLANE' ? 'Расписание авиарейсов' : 'Расписание междугородних автобусов'} — {direction === 'DEPARTURE' ? 'Отправление' : 'Прибытие'}
            </span>
          </div>
          <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
            Найдено рейсов: <strong style={{ color: '#38bdf8' }}>{trips.length}</strong>
          </span>
        </div>

        {loading ? (
          <div style={{ padding: '3rem', textAlign: 'center', color: '#94a3b8' }}>
            Загрузка актуального расписания...
          </div>
        ) : trips.length === 0 ? (
          <div style={{ padding: '3rem', textAlign: 'center', color: '#94a3b8' }}>
            Нет рейсов по заданным критериям фильтрации
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.875rem' }}>
              <thead>
                <tr style={{ background: 'rgba(15, 23, 42, 0.7)', borderBottom: '1px solid var(--border-color)', color: '#94a3b8', fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  <th style={{ padding: '0.85rem 1.25rem' }}>Время плановое</th>
                  <th style={{ padding: '0.85rem 1rem' }}>Расчётное / Факт</th>
                  <th style={{ padding: '0.85rem 1rem' }}>Рейс / Маршрут</th>
                  <th style={{ padding: '0.85rem 1rem' }}>Направление</th>
                  <th style={{ padding: '0.85rem 1rem' }}>Перевозчик</th>
                  <th style={{ padding: '0.85rem 1rem' }}>Сектор / Выход</th>
                  <th style={{ padding: '0.85rem 1rem' }}>Статус</th>
                  <th style={{ padding: '0.85rem 1.25rem', textAlign: 'right' }}>Действия</th>
                </tr>
              </thead>
              <tbody>
                {trips.map((t) => {
                  const isDeparture = direction === 'DEPARTURE';
                  const plannedTime = isDeparture ? t.schedule.departure_planned : t.schedule.arrival_planned;
                  const estimatedTime = isDeparture ? t.schedule.departure_estimated : t.schedule.arrival_estimated;
                  const hasDelay = t.status === 'DELAYED' && estimatedTime;
                  const origin = t.route.origin.city;
                  const dest = t.route.destination.city;

                  return (
                    <tr
                      key={t.id}
                      onClick={() => onSelectTrip(t)}
                      style={{
                        borderBottom: '1px solid var(--border-color)',
                        cursor: 'pointer',
                        transition: 'background 0.15s ease',
                      }}
                      onMouseEnter={(e) => (e.currentTarget.style.background = 'var(--bg-card-hover)')}
                      onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
                    >
                      {/* Planned Time */}
                      <td style={{ padding: '1rem 1.25rem' }}>
                        <div className="font-mono" style={{ fontWeight: 700, fontSize: '1rem', color: '#f8fafc' }}>
                          {formatTime(plannedTime)}
                        </div>
                        <div style={{ fontSize: '0.7rem', color: '#64748b' }}>
                          {formatDate(plannedTime)}
                        </div>
                      </td>

                      {/* Estimated Time */}
                      <td style={{ padding: '1rem 1rem' }}>
                        {hasDelay ? (
                          <div className="font-mono" style={{ fontWeight: 700, fontSize: '1rem', color: '#f59e0b' }}>
                            {formatTime(estimatedTime)}
                          </div>
                        ) : (
                          <span style={{ color: '#64748b' }}>—</span>
                        )}
                      </td>

                      {/* Trip Number */}
                      <td style={{ padding: '1rem 1rem' }}>
                        <div className="font-mono" style={{ fontWeight: 700, color: '#38bdf8' }}>
                          {t.trip_number}
                        </div>
                        <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
                          {t.transport_type === 'PLANE' ? 'Авиа' : 'Автобус'}
                        </div>
                      </td>

                      {/* Route */}
                      <td style={{ padding: '1rem 1rem' }}>
                        <div style={{ fontWeight: 600, color: '#f8fafc' }}>
                          {origin} → {dest}
                        </div>
                        <div style={{ fontSize: '0.75rem', color: '#64748b' }}>
                          {isDeparture ? t.route.destination.name : t.route.origin.name}
                        </div>
                      </td>

                      {/* Carrier */}
                      <td style={{ padding: '1rem 1rem', color: '#cbd5e1' }}>
                        {t.carrier.name}
                      </td>

                      {/* Gate / Platform */}
                      <td style={{ padding: '1rem 1rem' }}>
                        <span className="font-mono" style={{ background: '#0b1329', padding: '0.2rem 0.5rem', borderRadius: '0.25rem', border: '1px solid var(--border-color)', color: '#38bdf8', fontSize: '0.8rem' }}>
                          {t.gate_or_platform || '—'}
                        </span>
                      </td>

                      {/* Status */}
                      <td style={{ padding: '1rem 1rem' }}>
                        {getStatusBadge(t.status, t.weather_factor)}
                        {t.weather_factor?.has_impact && (
                          <div style={{ fontSize: '0.7rem', color: '#f59e0b', marginTop: '0.25rem', maxWidth: '180px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={t.weather_factor.phenomenon}>
                            ❄️ {t.weather_factor.phenomenon}
                          </div>
                        )}
                      </td>

                      {/* Actions */}
                      <td style={{ padding: '1rem 1.25rem', textAlign: 'right' }} onClick={(e) => e.stopPropagation()}>
                        <button
                          onClick={() => onSubscribeTrip(t)}
                          className="btn btn-secondary"
                          style={{ padding: '0.35rem 0.65rem', fontSize: '0.75rem' }}
                          title="Подписаться на SMS / Email уведомления о задержке рейса"
                        >
                          🔔 Подписаться
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
