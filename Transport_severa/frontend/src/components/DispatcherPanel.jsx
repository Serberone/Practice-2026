import React, { useState, useEffect } from 'react';
import { api } from '../api';

export default function DispatcherPanel() {
  const [trips, setTrips] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedTrip, setSelectedTrip] = useState(null);
  
  // Status Override Form state
  const [newStatus, setNewStatus] = useState('DELAYED');
  const [delayMinutes, setDelayMinutes] = useState(60);
  const [delayReason, setDelayReason] = useState('Метель и боковой ветер 18 м/с в пункте назначения');
  const [gateOrPlatform, setGateOrPlatform] = useState('');
  const [actionMsg, setActionMsg] = useState('');

  // Weather Ingestion Form state
  const [weatherCity, setWeatherCity] = useState('Усинск');
  const [tempC, setTempC] = useState(-26);
  const [windMs, setWindMs] = useState(18);
  const [visM, setVisM] = useState(500);
  const [phenomena, setPhenomena] = useState('Шквалистая низовая метель, снежные заносы');
  const [weatherRes, setWeatherRes] = useState(null);

  // Audit Logs
  const [auditLogs, setAuditLogs] = useState([]);

  useEffect(() => {
    loadAll();
  }, []);

  const loadAll = async () => {
    try {
      setLoading(true);
      const [tripsData, logsData] = await Promise.all([
        api.getTrips({ include_hidden: true }),
        api.getAuditLogs(),
      ]);
      setTrips(tripsData);
      setAuditLogs(logsData);
    } catch (e) {
      console.error('Error loading dispatcher data', e);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectForEdit = (t) => {
    setSelectedTrip(t);
    setNewStatus(t.status);
    setDelayReason(t.weather_factor?.phenomenon || '');
    setGateOrPlatform(t.gate_or_platform || '');
    setActionMsg('');
  };

  const handleSubmitOverride = async (e) => {
    e.preventDefault();
    if (!selectedTrip) return;
    try {
      await api.overrideStatus(selectedTrip.id, {
        status: newStatus,
        delay_minutes: newStatus === 'DELAYED' ? parseInt(delayMinutes, 10) : 0,
        delay_reason: delayReason,
        gate_or_platform: gateOrPlatform,
      });
      setActionMsg(`✓ Статус рейса ${selectedTrip.trip_number} успешно обновлён! Уведомления разосланы пассажирам.`);
      loadAll();
    } catch (err) {
      setActionMsg(`✕ Ошибка: ${err.message}`);
    }
  };

  const handleToggleHide = async (t) => {
    try {
      const isHidden = !t.display_flags?.is_hidden;
      await api.hideTrip(t.id, isHidden);
      loadAll();
    } catch (err) {
      alert(`Ошибка изменения видимости: ${err.message}`);
    }
  };

  const handleVerifyTrip = async (t) => {
    try {
      await api.verifyTrip(t.id);
      loadAll();
    } catch (err) {
      alert(`Ошибка подтверждения публикации: ${err.message}`);
    }
  };

  const handleSendWeather = async (e) => {
    e.preventDefault();
    try {
      const res = await api.ingestWeather(weatherCity, {
        temperature_c: parseFloat(tempC),
        wind_speed_ms: parseFloat(windMs),
        visibility_meters: parseInt(visM, 10),
        phenomena: phenomena,
      });
      setWeatherRes(res);
      loadAll();
    } catch (err) {
      alert(`Ошибка отправки метеоданных: ${err.message}`);
    }
  };

  return (
    <div className="container" style={{ padding: '2rem 1rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 800, color: '#f8fafc' }}>
            🎧 Рабочее место дежурного диспетчера
          </h2>
          <p style={{ fontSize: '0.85rem', color: '#94a3b8' }}>
            Оперативное управление расписанием, обработка погодных задержек и публикация на табло
          </p>
        </div>
        <button onClick={loadAll} className="btn btn-secondary">
          🔄 Обновить данные
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 380px', gap: '1.5rem' }}>
        {/* Left Column: Trips Table with operational controls */}
        <div>
          <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: '0.75rem', overflow: 'hidden', marginBottom: '1.5rem' }}>
            <div style={{ padding: '0.85rem 1.25rem', background: '#0b1329', borderBottom: '1px solid var(--border-color)', fontWeight: 600, color: '#f8fafc' }}>
              Мониторинг и оперативное управление рейсами
            </div>
            {loading ? (
              <div style={{ padding: '2rem', textAlign: 'center', color: '#94a3b8' }}>Загрузка рейсов...</div>
            ) : (
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.825rem', textAlign: 'left' }}>
                  <thead>
                    <tr style={{ background: 'rgba(15, 23, 42, 0.7)', borderBottom: '1px solid var(--border-color)', color: '#94a3b8' }}>
                      <th style={{ padding: '0.75rem 1rem' }}>Рейс</th>
                      <th style={{ padding: '0.75rem 0.75rem' }}>Маршрут</th>
                      <th style={{ padding: '0.75rem 0.75rem' }}>Статус</th>
                      <th style={{ padding: '0.75rem 0.75rem' }}>Метео</th>
                      <th style={{ padding: '0.75rem 0.75rem' }}>Табло</th>
                      <th style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>Управление</th>
                    </tr>
                  </thead>
                  <tbody>
                    {trips.map((t) => {
                      const isReviewNeeded = t.display_flags?.requires_dispatcher_review;
                      const isHidden = t.display_flags?.is_hidden;
                      return (
                        <tr
                          key={t.id}
                          style={{
                            borderBottom: '1px solid var(--border-color)',
                            background: isReviewNeeded ? 'rgba(245, 158, 11, 0.08)' : isHidden ? 'rgba(15, 23, 42, 0.4)' : 'transparent'
                          }}
                        >
                          <td style={{ padding: '0.75rem 1rem' }}>
                            <div className="font-mono" style={{ fontWeight: 700, color: '#38bdf8' }}>{t.trip_number}</div>
                            <div style={{ fontSize: '0.7rem', color: '#64748b' }}>{t.transport_type}</div>
                          </td>
                          <td style={{ padding: '0.75rem 0.75rem' }}>
                            <div>{t.route.origin.city} → {t.route.destination.city}</div>
                          </td>
                          <td style={{ padding: '0.75rem 0.75rem' }}>
                            <span style={{
                              color: t.status === 'DELAYED' ? '#fbbf24' : t.status === 'CANCELLED' ? '#f87171' : t.status === 'BOARDING' ? '#34d399' : '#38bdf8',
                              fontWeight: 600
                            }}>
                              {t.status}
                            </span>
                          </td>
                          <td style={{ padding: '0.75rem 0.75rem' }}>
                            {t.weather_factor?.has_impact ? (
                              <span style={{ color: '#fbbf24', fontSize: '0.75rem' }} title={t.weather_factor.phenomenon}>
                                ⚠️ Угроза
                              </span>
                            ) : (
                              <span style={{ color: '#10b981', fontSize: '0.75rem' }}>Норма</span>
                            )}
                          </td>
                          <td style={{ padding: '0.75rem 0.75rem' }}>
                            {isHidden ? (
                              <span style={{ color: '#ef4444', fontSize: '0.75rem' }}>Скрыт</span>
                            ) : (
                              <span style={{ color: '#10b981', fontSize: '0.75rem' }}>Отображается</span>
                            )}
                          </td>
                          <td style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>
                            <div style={{ display: 'flex', gap: '0.35rem', justifyContent: 'flex-end' }}>
                              {isReviewNeeded && (
                                <button
                                  onClick={() => handleVerifyTrip(t)}
                                  className="btn btn-primary"
                                  style={{ padding: '0.25rem 0.5rem', fontSize: '0.7rem' }}
                                  title="Подтвердить публикацию рейса на табло"
                                >
                                  ✓ Одобрить
                                </button>
                              )}
                              <button
                                onClick={() => handleSelectForEdit(t)}
                                className="btn btn-secondary"
                                style={{ padding: '0.25rem 0.5rem', fontSize: '0.7rem' }}
                              >
                                ✏️ Изменить
                              </button>
                              <button
                                onClick={() => handleToggleHide(t)}
                                className="btn"
                                style={{
                                  padding: '0.25rem 0.5rem',
                                  fontSize: '0.7rem',
                                  background: isHidden ? '#10b981' : '#334155',
                                  color: '#fff'
                                }}
                              >
                                {isHidden ? 'Показать' : 'Скрыть'}
                              </button>
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Audit Logs Table */}
          <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: '0.75rem', overflow: 'hidden' }}>
            <div style={{ padding: '0.85rem 1.25rem', background: '#0b1329', borderBottom: '1px solid var(--border-color)', fontWeight: 600, color: '#f8fafc' }}>
              📜 Журнал аудита действий (Audit Log)
            </div>
            <div style={{ maxHeight: '240px', overflowY: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.775rem', textAlign: 'left' }}>
                <thead>
                  <tr style={{ background: 'rgba(15, 23, 42, 0.7)', borderBottom: '1px solid var(--border-color)', color: '#94a3b8' }}>
                    <th style={{ padding: '0.5rem 0.75rem' }}>Время</th>
                    <th style={{ padding: '0.5rem 0.75rem' }}>Оператор</th>
                    <th style={{ padding: '0.5rem 0.75rem' }}>Событие</th>
                    <th style={{ padding: '0.5rem 0.75rem' }}>Детали</th>
                  </tr>
                </thead>
                <tbody>
                  {auditLogs.slice(0, 15).map((log, idx) => (
                    <tr key={idx} style={{ borderBottom: '1px solid var(--border-color)' }}>
                      <td className="font-mono" style={{ padding: '0.5rem 0.75rem', color: '#94a3b8' }}>
                        {new Date(log.timestamp).toLocaleTimeString('ru-RU')}
                      </td>
                      <td style={{ padding: '0.5rem 0.75rem', color: '#38bdf8' }}>{log.username || 'Система'}</td>
                      <td style={{ padding: '0.5rem 0.75rem', fontWeight: 600 }}>{log.event_type}</td>
                      <td style={{ padding: '0.5rem 0.75rem', color: '#cbd5e1' }}>
                        {log.details?.trip_number && <span>Рейс {log.details.trip_number}: </span>}
                        {log.details?.new_status && <span>{log.details.old_status} → {log.details.new_status}; </span>}
                        {log.details?.reason && <span>{log.details.reason}</span>}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Right Column: Actions (Status Override & Weather Ingestion) */}
        <div>
          {/* Status Override Panel */}
          <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: '0.75rem', padding: '1.25rem', marginBottom: '1.5rem' }}>
            <h3 style={{ fontSize: '1rem', fontWeight: 700, color: '#f8fafc', marginBottom: '0.85rem' }}>
              ⚡ Ручная корректировка рейса
            </h3>
            {selectedTrip ? (
              <form onSubmit={handleSubmitOverride}>
                <div style={{ background: '#0b1329', padding: '0.65rem 0.85rem', borderRadius: '0.375rem', border: '1px solid var(--border-color)', marginBottom: '1rem' }}>
                  <div className="font-mono" style={{ fontWeight: 700, color: '#38bdf8' }}>
                    {selectedTrip.trip_number} ({selectedTrip.route.origin.city} → {selectedTrip.route.destination.city})
                  </div>
                  <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Текущий статус: {selectedTrip.status}</div>
                </div>

                <div style={{ marginBottom: '0.85rem' }}>
                  <label style={{ display: 'block', fontSize: '0.75rem', color: '#94a3b8', marginBottom: '0.25rem' }}>Новый статус рейса:</label>
                  <select
                    value={newStatus}
                    onChange={(e) => setNewStatus(e.target.value)}
                    style={{ width: '100%', background: '#0b1329', color: '#f8fafc', border: '1px solid var(--border-color)', borderRadius: '0.375rem', padding: '0.45rem', fontSize: '0.85rem' }}
                  >
                    <option value="SCHEDULED">SCHEDULED (По расписанию)</option>
                    <option value="BOARDING">BOARDING (Идёт посадка)</option>
                    <option value="DELAYED">DELAYED (Задержан)</option>
                    <option value="CANCELLED">CANCELLED (Отменён)</option>
                    <option value="ARRIVED">ARRIVED (Прибыл)</option>
                    <option value="DEPARTED">DEPARTED (Отправлен)</option>
                  </select>
                </div>

                {newStatus === 'DELAYED' && (
                  <div style={{ marginBottom: '0.85rem' }}>
                    <label style={{ display: 'block', fontSize: '0.75rem', color: '#94a3b8', marginBottom: '0.25rem' }}>Время задержки (минут):</label>
                    <input
                      type="number"
                      value={delayMinutes}
                      onChange={(e) => setDelayMinutes(e.target.value)}
                      style={{ width: '100%', background: '#0b1329', color: '#f8fafc', border: '1px solid var(--border-color)', borderRadius: '0.375rem', padding: '0.45rem', fontSize: '0.85rem' }}
                    />
                  </div>
                )}

                <div style={{ marginBottom: '0.85rem' }}>
                  <label style={{ display: 'block', fontSize: '0.75rem', color: '#94a3b8', marginBottom: '0.25rem' }}>Причина задержки / комментарий:</label>
                  <textarea
                    rows={2}
                    value={delayReason}
                    onChange={(e) => setDelayReason(e.target.value)}
                    style={{ width: '100%', background: '#0b1329', color: '#f8fafc', border: '1px solid var(--border-color)', borderRadius: '0.375rem', padding: '0.45rem', fontSize: '0.85rem' }}
                  />
                </div>

                <div style={{ marginBottom: '1rem' }}>
                  <label style={{ display: 'block', fontSize: '0.75rem', color: '#94a3b8', marginBottom: '0.25rem' }}>Выход / сектор / платформа:</label>
                  <input
                    type="text"
                    value={gateOrPlatform}
                    onChange={(e) => setGateOrPlatform(e.target.value)}
                    placeholder="Сектор 2 или Платформа 1"
                    style={{ width: '100%', background: '#0b1329', color: '#f8fafc', border: '1px solid var(--border-color)', borderRadius: '0.375rem', padding: '0.45rem', fontSize: '0.85rem' }}
                  />
                </div>

                {actionMsg && (
                  <div style={{ fontSize: '0.775rem', padding: '0.5rem', borderRadius: '0.375rem', marginBottom: '0.75rem', background: actionMsg.startsWith('✓') ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)', color: actionMsg.startsWith('✓') ? '#34d399' : '#f87171' }}>
                    {actionMsg}
                  </div>
                )}

                <button type="submit" className="btn btn-primary" style={{ width: '100%' }}>
                  Применить изменение и оповестить
                </button>
              </form>
            ) : (
              <div style={{ fontSize: '0.825rem', color: '#94a3b8', textAlign: 'center', padding: '1.5rem 0' }}>
                Выберите рейс в таблице слева (кнопка «Изменить»)
              </div>
            )}
          </div>

          {/* Weather Simulation / Ingest Panel */}
          <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: '0.75rem', padding: '1.25rem' }}>
            <h3 style={{ fontSize: '1rem', fontWeight: 700, color: '#f8fafc', marginBottom: '0.85rem' }}>
              🌪️ Ввод оперативной метеосводки
            </h3>
            <form onSubmit={handleSendWeather}>
              <div style={{ marginBottom: '0.65rem' }}>
                <label style={{ display: 'block', fontSize: '0.75rem', color: '#94a3b8', marginBottom: '0.25rem' }}>Город:</label>
                <select
                  value={weatherCity}
                  onChange={(e) => setWeatherCity(e.target.value)}
                  style={{ width: '100%', background: '#0b1329', color: '#f8fafc', border: '1px solid var(--border-color)', borderRadius: '0.375rem', padding: '0.45rem', fontSize: '0.85rem' }}
                >
                  <option value="Сыктывкар">Сыктывкар</option>
                  <option value="Усинск">Усинск</option>
                  <option value="Ухта">Ухта</option>
                  <option value="Печора">Печора</option>
                </select>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', marginBottom: '0.65rem' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.75rem', color: '#94a3b8', marginBottom: '0.25rem' }}>Темп-ра (°C):</label>
                  <input
                    type="number"
                    value={tempC}
                    onChange={(e) => setTempC(e.target.value)}
                    style={{ width: '100%', background: '#0b1329', color: '#f8fafc', border: '1px solid var(--border-color)', borderRadius: '0.375rem', padding: '0.45rem', fontSize: '0.85rem' }}
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.75rem', color: '#94a3b8', marginBottom: '0.25rem' }}>Ветер (м/с):</label>
                  <input
                    type="number"
                    value={windMs}
                    onChange={(e) => setWindMs(e.target.value)}
                    style={{ width: '100%', background: '#0b1329', color: '#f8fafc', border: '1px solid var(--border-color)', borderRadius: '0.375rem', padding: '0.45rem', fontSize: '0.85rem' }}
                  />
                </div>
              </div>

              <div style={{ marginBottom: '0.65rem' }}>
                <label style={{ display: 'block', fontSize: '0.75rem', color: '#94a3b8', marginBottom: '0.25rem' }}>Видимость (метров):</label>
                <input
                  type="number"
                  value={visM}
                  onChange={(e) => setVisM(e.target.value)}
                  style={{ width: '100%', background: '#0b1329', color: '#f8fafc', border: '1px solid var(--border-color)', borderRadius: '0.375rem', padding: '0.45rem', fontSize: '0.85rem' }}
                />
              </div>

              <div style={{ marginBottom: '0.85rem' }}>
                <label style={{ display: 'block', fontSize: '0.75rem', color: '#94a3b8', marginBottom: '0.25rem' }}>Явления:</label>
                <input
                  type="text"
                  value={phenomena}
                  onChange={(e) => setPhenomena(e.target.value)}
                  style={{ width: '100%', background: '#0b1329', color: '#f8fafc', border: '1px solid var(--border-color)', borderRadius: '0.375rem', padding: '0.45rem', fontSize: '0.85rem' }}
                />
              </div>

              {weatherRes && (
                <div style={{ fontSize: '0.75rem', padding: '0.5rem', borderRadius: '0.375rem', marginBottom: '0.75rem', background: weatherRes.evaluation?.alert_level === 'SEVERE' ? 'rgba(239,68,68,0.15)' : 'rgba(16,185,129,0.15)', color: weatherRes.evaluation?.alert_level === 'SEVERE' ? '#f87171' : '#34d399' }}>
                  Оценка системы: <strong>{weatherRes.evaluation?.alert_level}</strong>
                  {weatherRes.evaluation?.flight_critical && <div>✈️ Критично для авиации</div>}
                  {weatherRes.evaluation?.bus_critical && <div>🚌 Критично для автобусов</div>}
                </div>
              )}

              <button type="submit" className="btn btn-secondary" style={{ width: '100%' }}>
                Зарегистрировать сводку
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
