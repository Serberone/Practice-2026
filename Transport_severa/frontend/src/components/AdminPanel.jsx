import React, { useState, useEffect } from 'react';
import { api } from '../api';

export default function AdminPanel() {
  const [activeTab, setActiveTab] = useState('users'); // users | directories | integrations
  
  // Users state
  const [users, setUsers] = useState([]);
  const [newUsername, setNewUsername] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [newFullName, setNewFullName] = useState('');
  const [newRole, setNewRole] = useState('DISPATCHER');
  const [userMsg, setUserMsg] = useState('');

  // Directories state
  const [stations, setStations] = useState([]);
  const [carriers, setCarriers] = useState([]);
  const [dirMsg, setDirMsg] = useState('');
  
  // Station form (create / edit)
  const [editingStationId, setEditingStationId] = useState(null);
  const [stName, setStName] = useState('');
  const [stCity, setStCity] = useState('Сыктывкар');
  const [stType, setStType] = useState('AIRPORT');
  const [stCode, setStCode] = useState('');

  // Carrier form (create / edit)
  const [editingCarrierId, setEditingCarrierId] = useState(null);
  const [carName, setCarName] = useState('');
  const [carShort, setCarShort] = useState('');
  const [carType, setCarType] = useState('AIR');
  const [carPhone, setCarPhone] = useState('');
  const [carInn, setCarInn] = useState('');

  // Integrations state
  const [syncStatus, setSyncStatus] = useState(null);
  const [syncMsg, setSyncMsg] = useState('');

  useEffect(() => {
    loadAll();
  }, [activeTab]);

  const loadAll = async () => {
    try {
      if (activeTab === 'users') {
        const u = await api.getUsers();
        setUsers(u);
      } else if (activeTab === 'directories') {
        const [st, ca] = await Promise.all([
          api.getStations({ include_inactive: 'true' }),
          api.getCarriers(),
        ]);
        setStations(st);
        setCarriers(ca);
      } else if (activeTab === 'integrations') {
        const s = await api.getSyncStatus();
        setSyncStatus(s);
      }
    } catch (e) {
      console.error('Error loading admin data', e);
    }
  };

  const handleCreateUser = async (e) => {
    e.preventDefault();
    try {
      await api.createUser({
        username: newUsername,
        password: newPassword,
        full_name: newFullName,
        role: newRole,
      });
      setUserMsg('✓ Пользователь успешно создан');
      setNewUsername('');
      setNewPassword('');
      setNewFullName('');
      const u = await api.getUsers();
      setUsers(u);
    } catch (err) {
      setUserMsg(`✕ Ошибка: ${err.message}`);
    }
  };

  const resetStationForm = () => {
    setEditingStationId(null);
    setStName('');
    setStCity('Сыктывкар');
    setStType('AIRPORT');
    setStCode('');
  };

  const resetCarrierForm = () => {
    setEditingCarrierId(null);
    setCarName('');
    setCarShort('');
    setCarType('AIR');
    setCarPhone('');
    setCarInn('');
  };

  const startEditStation = (station) => {
    setEditingStationId(station.id);
    setStName(station.name || '');
    setStCity(station.city || '');
    setStType(station.type || 'AIRPORT');
    setStCode(station.code || '');
    setDirMsg('');
  };

  const startEditCarrier = (carrier) => {
    setEditingCarrierId(carrier.id);
    setCarName(carrier.name || '');
    setCarShort(carrier.short_name || '');
    setCarType(carrier.transport_type || 'AIR');
    setCarPhone(carrier.phone || '');
    setCarInn(carrier.inn || '');
    setDirMsg('');
  };

  const handleSaveStation = async (e) => {
    e.preventDefault();
    const payload = {
      name: stName,
      city: stCity,
      type: stType,
      code: stCode,
      is_active: true,
    };
    try {
      if (editingStationId) {
        await api.updateStation(editingStationId, payload);
        setDirMsg('✓ Станция обновлена');
      } else {
        await api.createStation(payload);
        setDirMsg('✓ Станция добавлена');
      }
      resetStationForm();
      const st = await api.getStations({ include_inactive: 'true' });
      setStations(st);
    } catch (err) {
      setDirMsg(`✕ Ошибка станции: ${err.message}`);
    }
  };

  const handleDeleteStation = async (station) => {
    if (!window.confirm(`Удалить станцию «${station.name}»?`)) return;
    try {
      await api.deleteStation(station.id);
      if (editingStationId === station.id) resetStationForm();
      setDirMsg('✓ Станция удалена');
      const st = await api.getStations({ include_inactive: 'true' });
      setStations(st);
    } catch (err) {
      setDirMsg(`✕ Ошибка удаления станции: ${err.message}`);
    }
  };

  const handleSaveCarrier = async (e) => {
    e.preventDefault();
    const payload = {
      name: carName,
      short_name: carShort,
      transport_type: carType,
      phone: carPhone,
      inn: carInn,
    };
    try {
      if (editingCarrierId) {
        await api.updateCarrier(editingCarrierId, payload);
        setDirMsg('✓ Перевозчик обновлён');
      } else {
        await api.createCarrier(payload);
        setDirMsg('✓ Перевозчик добавлен');
      }
      resetCarrierForm();
      const ca = await api.getCarriers();
      setCarriers(ca);
    } catch (err) {
      setDirMsg(`✕ Ошибка перевозчика: ${err.message}`);
    }
  };

  const handleDeleteCarrier = async (carrier) => {
    if (!window.confirm(`Удалить перевозчика «${carrier.name}»?`)) return;
    try {
      await api.deleteCarrier(carrier.id);
      if (editingCarrierId === carrier.id) resetCarrierForm();
      setDirMsg('✓ Перевозчик удалён');
      const ca = await api.getCarriers();
      setCarriers(ca);
    } catch (err) {
      setDirMsg(`✕ Ошибка удаления перевозчика: ${err.message}`);
    }
  };

  const handleSeed = async () => {
    try {
      setSyncMsg('Инициализация базы данных...');
      const res = await api.seedData();
      setSyncMsg(`✓ ${res.message}`);
    } catch (err) {
      setSyncMsg(`✕ Ошибка: ${err.message}`);
    }
  };

  const handleSyncYandex = async () => {
    try {
      setSyncMsg('Выполняется синхронизация с API Яндекс.Расписаний...');
      const res = await api.syncYandex();
      const routeLines = (res.details || [])
        .map((item) => `${item.route}: ${item.segments_count} рейсов`)
        .join('; ');
      setSyncMsg(`✓ ${res.message}${routeLines ? `. ${routeLines}` : ''}`);
      try {
        const s = await api.getSyncStatus();
        setSyncStatus(s);
      } catch (statusErr) {
        console.error('Не удалось обновить статус синка', statusErr);
      }
    } catch (err) {
      setSyncMsg(`✕ Ошибка: ${err.message}`);
    }
  };

  return (
    <div className="container" style={{ padding: '2rem 1rem' }}>
      <div style={{ marginBottom: '1.5rem' }}>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 800, color: '#f8fafc' }}>
          ⚙️ Панель системного администратора
        </h2>
        <p style={{ fontSize: '0.85rem', color: '#94a3b8' }}>
          Управление учетными записями, справочниками транспорта и интеграционными шлюзами
        </p>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '0.5rem', borderBottom: '1px solid var(--border-color)', marginBottom: '1.5rem' }}>
        <button
          onClick={() => setActiveTab('users')}
          className="btn"
          style={{
            background: activeTab === 'users' ? '#1e293b' : 'transparent',
            color: activeTab === 'users' ? '#38bdf8' : '#94a3b8',
            borderBottom: activeTab === 'users' ? '2px solid #38bdf8' : 'none',
            borderRadius: '0.5rem 0.5rem 0 0'
          }}
        >
          👥 Пользователи и права
        </button>
        <button
          onClick={() => setActiveTab('directories')}
          className="btn"
          style={{
            background: activeTab === 'directories' ? '#1e293b' : 'transparent',
            color: activeTab === 'directories' ? '#38bdf8' : '#94a3b8',
            borderBottom: activeTab === 'directories' ? '2px solid #38bdf8' : 'none',
            borderRadius: '0.5rem 0.5rem 0 0'
          }}
        >
          📚 Справочники (НСИ)
        </button>
        <button
          onClick={() => setActiveTab('integrations')}
          className="btn"
          style={{
            background: activeTab === 'integrations' ? '#1e293b' : 'transparent',
            color: activeTab === 'integrations' ? '#38bdf8' : '#94a3b8',
            borderBottom: activeTab === 'integrations' ? '2px solid #38bdf8' : 'none',
            borderRadius: '0.5rem 0.5rem 0 0'
          }}
        >
          🌐 Интеграции и шлюзы
        </button>
      </div>

      {/* USERS TAB */}
      {activeTab === 'users' && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 360px', gap: '1.5rem' }}>
          <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: '0.75rem', overflow: 'hidden' }}>
            <div style={{ padding: '0.85rem 1.25rem', background: '#0b1329', borderBottom: '1px solid var(--border-color)', fontWeight: 600 }}>
              Список пользователей системы
            </div>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem', textAlign: 'left' }}>
              <thead>
                <tr style={{ background: 'rgba(15, 23, 42, 0.7)', borderBottom: '1px solid var(--border-color)', color: '#94a3b8' }}>
                  <th style={{ padding: '0.75rem 1rem' }}>Логин</th>
                  <th style={{ padding: '0.75rem 1rem' }}>ФИО / Должность</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Роль</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Статус</th>
                </tr>
              </thead>
              <tbody>
                {users.map((u, i) => (
                  <tr key={i} style={{ borderBottom: '1px solid var(--border-color)' }}>
                    <td className="font-mono" style={{ padding: '0.75rem 1rem', color: '#38bdf8', fontWeight: 600 }}>{u.username}</td>
                    <td style={{ padding: '0.75rem 1rem', color: '#f8fafc' }}>{u.full_name}</td>
                    <td style={{ padding: '0.75rem 1rem' }}>
                      <span className="badge" style={{ background: u.role === 'ADMIN' ? 'rgba(168,85,247,0.2)' : 'rgba(245,158,11,0.2)', color: u.role === 'ADMIN' ? '#c084fc' : '#fbbf24' }}>
                        {u.role}
                      </span>
                    </td>
                    <td style={{ padding: '0.75rem 1rem' }}>
                      <span style={{ color: u.is_active ? '#34d399' : '#f87171' }}>
                        {u.is_active ? 'Активен' : 'Заблокирован'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: '0.75rem', padding: '1.25rem' }}>
            <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '1rem' }}>Добавить пользователя</h3>
            <form onSubmit={handleCreateUser}>
              <div style={{ marginBottom: '0.75rem' }}>
                <label style={{ display: 'block', fontSize: '0.75rem', color: '#94a3b8', marginBottom: '0.25rem' }}>Логин:</label>
                <input
                  type="text"
                  required
                  value={newUsername}
                  onChange={(e) => setNewUsername(e.target.value)}
                  style={{ width: '100%', background: '#0b1329', color: '#f8fafc', border: '1px solid var(--border-color)', borderRadius: '0.375rem', padding: '0.45rem', fontSize: '0.85rem' }}
                />
              </div>
              <div style={{ marginBottom: '0.75rem' }}>
                <label style={{ display: 'block', fontSize: '0.75rem', color: '#94a3b8', marginBottom: '0.25rem' }}>Пароль:</label>
                <input
                  type="password"
                  required
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  style={{ width: '100%', background: '#0b1329', color: '#f8fafc', border: '1px solid var(--border-color)', borderRadius: '0.375rem', padding: '0.45rem', fontSize: '0.85rem' }}
                />
              </div>
              <div style={{ marginBottom: '0.75rem' }}>
                <label style={{ display: 'block', fontSize: '0.75rem', color: '#94a3b8', marginBottom: '0.25rem' }}>ФИО / Назначение:</label>
                <input
                  type="text"
                  required
                  value={newFullName}
                  onChange={(e) => setNewFullName(e.target.value)}
                  style={{ width: '100%', background: '#0b1329', color: '#f8fafc', border: '1px solid var(--border-color)', borderRadius: '0.375rem', padding: '0.45rem', fontSize: '0.85rem' }}
                />
              </div>
              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', fontSize: '0.75rem', color: '#94a3b8', marginBottom: '0.25rem' }}>Роль:</label>
                <select
                  value={newRole}
                  onChange={(e) => setNewRole(e.target.value)}
                  style={{ width: '100%', background: '#0b1329', color: '#f8fafc', border: '1px solid var(--border-color)', borderRadius: '0.375rem', padding: '0.45rem', fontSize: '0.85rem' }}
                >
                  <option value="DISPATCHER">DISPATCHER (Диспетчер)</option>
                  <option value="ADMIN">ADMIN (Администратор)</option>
                </select>
              </div>

              {userMsg && (
                <div style={{ fontSize: '0.775rem', padding: '0.5rem', borderRadius: '0.375rem', marginBottom: '0.75rem', background: userMsg.startsWith('✓') ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)', color: userMsg.startsWith('✓') ? '#34d399' : '#f87171' }}>
                  {userMsg}
                </div>
              )}

              <button type="submit" className="btn btn-primary" style={{ width: '100%' }}>
                Зарегистрировать пользователя
              </button>
            </form>
          </div>
        </div>
      )}

      {/* DIRECTORIES TAB */}
      {activeTab === 'directories' && (
        <div>
          {dirMsg && (
            <div style={{ fontSize: '0.825rem', padding: '0.65rem 0.85rem', borderRadius: '0.5rem', marginBottom: '1rem', background: dirMsg.startsWith('✓') ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)', color: dirMsg.startsWith('✓') ? '#34d399' : '#f87171', border: '1px solid var(--border-color)' }}>
              {dirMsg}
            </div>
          )}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
            {/* Stations */}
            <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: '0.75rem', padding: '1.25rem' }}>
              <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '0.75rem' }}>Справочник станций и узлов</h3>
              <div style={{ maxHeight: '280px', overflowY: 'auto', marginBottom: '1rem' }}>
                {stations.map((s) => (
                  <div key={s.id || s.code} style={{ padding: '0.65rem 0', borderBottom: '1px solid var(--border-color)', fontSize: '0.825rem', display: 'flex', justifyContent: 'space-between', gap: '0.75rem', alignItems: 'flex-start' }}>
                    <div style={{ minWidth: 0 }}>
                      <div style={{ fontWeight: 600, color: '#f8fafc' }}>{s.name}</div>
                      <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>г. {s.city} | Код: {s.code} | Тип: {s.type}</div>
                    </div>
                    <div style={{ display: 'flex', gap: '0.35rem', flexShrink: 0 }}>
                      <button type="button" className="btn btn-secondary" style={{ padding: '0.2rem 0.5rem', fontSize: '0.7rem' }} onClick={() => startEditStation(s)}>Изменить</button>
                      <button type="button" className="btn btn-danger" style={{ padding: '0.2rem 0.5rem', fontSize: '0.7rem' }} onClick={() => handleDeleteStation(s)}>Удалить</button>
                    </div>
                  </div>
                ))}
              </div>
              <form onSubmit={handleSaveStation} style={{ background: '#0b1329', padding: '0.75rem', borderRadius: '0.5rem', border: '1px solid var(--border-color)' }}>
                <div style={{ fontSize: '0.8rem', fontWeight: 600, marginBottom: '0.5rem', color: '#38bdf8' }}>
                  {editingStationId ? '✎ Редактирование станции' : '+ Добавить станцию / узел'}
                </div>
                <input placeholder="Название (напр. Аэропорт Воркута)" value={stName} onChange={e => setStName(e.target.value)} required style={{ width: '100%', marginBottom: '0.5rem', background: '#1e293b', color: '#fff', border: '1px solid var(--border-color)', padding: '0.4rem', borderRadius: '0.25rem', fontSize: '0.8rem' }} />
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '0.5rem', marginBottom: '0.5rem' }}>
                  <input placeholder="Город" value={stCity} onChange={e => setStCity(e.target.value)} required style={{ background: '#1e293b', color: '#fff', border: '1px solid var(--border-color)', padding: '0.4rem', borderRadius: '0.25rem', fontSize: '0.8rem' }} />
                  <select value={stType} onChange={e => setStType(e.target.value)} style={{ background: '#1e293b', color: '#fff', border: '1px solid var(--border-color)', padding: '0.4rem', borderRadius: '0.25rem', fontSize: '0.8rem' }}>
                    <option value="AIRPORT">AIRPORT</option>
                    <option value="BUS_STATION">BUS_STATION</option>
                  </select>
                  <input placeholder="Код (VKT)" value={stCode} onChange={e => setStCode(e.target.value)} required style={{ background: '#1e293b', color: '#fff', border: '1px solid var(--border-color)', padding: '0.4rem', borderRadius: '0.25rem', fontSize: '0.8rem' }} />
                </div>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  <button type="submit" className="btn btn-secondary" style={{ flex: 1, fontSize: '0.75rem', padding: '0.35rem' }}>
                    {editingStationId ? 'Сохранить изменения' : 'Добавить узел'}
                  </button>
                  {editingStationId && (
                    <button type="button" className="btn btn-secondary" style={{ fontSize: '0.75rem', padding: '0.35rem 0.75rem' }} onClick={resetStationForm}>
                      Отмена
                    </button>
                  )}
                </div>
              </form>
            </div>

            {/* Carriers */}
            <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: '0.75rem', padding: '1.25rem' }}>
              <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '0.75rem' }}>Справочник перевозчиков</h3>
              <div style={{ maxHeight: '280px', overflowY: 'auto', marginBottom: '1rem' }}>
                {carriers.map((c) => (
                  <div key={c.id || c.inn} style={{ padding: '0.65rem 0', borderBottom: '1px solid var(--border-color)', fontSize: '0.825rem', display: 'flex', justifyContent: 'space-between', gap: '0.75rem', alignItems: 'flex-start' }}>
                    <div style={{ minWidth: 0 }}>
                      <div style={{ fontWeight: 600, color: '#f8fafc' }}>{c.name} ({c.short_name})</div>
                      <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Тип: {c.transport_type} | ИНН: {c.inn} | Тел: {c.phone}</div>
                    </div>
                    <div style={{ display: 'flex', gap: '0.35rem', flexShrink: 0 }}>
                      <button type="button" className="btn btn-secondary" style={{ padding: '0.2rem 0.5rem', fontSize: '0.7rem' }} onClick={() => startEditCarrier(c)}>Изменить</button>
                      <button type="button" className="btn btn-danger" style={{ padding: '0.2rem 0.5rem', fontSize: '0.7rem' }} onClick={() => handleDeleteCarrier(c)}>Удалить</button>
                    </div>
                  </div>
                ))}
              </div>
              <form onSubmit={handleSaveCarrier} style={{ background: '#0b1329', padding: '0.75rem', borderRadius: '0.5rem', border: '1px solid var(--border-color)' }}>
                <div style={{ fontSize: '0.8rem', fontWeight: 600, marginBottom: '0.5rem', color: '#38bdf8' }}>
                  {editingCarrierId ? '✎ Редактирование перевозчика' : '+ Добавить перевозчика'}
                </div>
                <input placeholder="Полное наименование предприятия" value={carName} onChange={e => setCarName(e.target.value)} required style={{ width: '100%', marginBottom: '0.5rem', background: '#1e293b', color: '#fff', border: '1px solid var(--border-color)', padding: '0.4rem', borderRadius: '0.25rem', fontSize: '0.8rem' }} />
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', marginBottom: '0.5rem' }}>
                  <input placeholder="Краткое назв." value={carShort} onChange={e => setCarShort(e.target.value)} required style={{ background: '#1e293b', color: '#fff', border: '1px solid var(--border-color)', padding: '0.4rem', borderRadius: '0.25rem', fontSize: '0.8rem' }} />
                  <select value={carType} onChange={e => setCarType(e.target.value)} style={{ background: '#1e293b', color: '#fff', border: '1px solid var(--border-color)', padding: '0.4rem', borderRadius: '0.25rem', fontSize: '0.8rem' }}>
                    <option value="AIR">AIR (Авиа)</option>
                    <option value="BUS">BUS (Автобус)</option>
                  </select>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', marginBottom: '0.5rem' }}>
                  <input placeholder="Телефон диспетчерской" value={carPhone} onChange={e => setCarPhone(e.target.value)} style={{ background: '#1e293b', color: '#fff', border: '1px solid var(--border-color)', padding: '0.4rem', borderRadius: '0.25rem', fontSize: '0.8rem' }} />
                  <input placeholder="ИНН" value={carInn} onChange={e => setCarInn(e.target.value)} style={{ background: '#1e293b', color: '#fff', border: '1px solid var(--border-color)', padding: '0.4rem', borderRadius: '0.25rem', fontSize: '0.8rem' }} />
                </div>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  <button type="submit" className="btn btn-secondary" style={{ flex: 1, fontSize: '0.75rem', padding: '0.35rem' }}>
                    {editingCarrierId ? 'Сохранить изменения' : 'Добавить перевозчика'}
                  </button>
                  {editingCarrierId && (
                    <button type="button" className="btn btn-secondary" style={{ fontSize: '0.75rem', padding: '0.35rem 0.75rem' }} onClick={resetCarrierForm}>
                      Отмена
                    </button>
                  )}
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* INTEGRATIONS TAB */}
      {activeTab === 'integrations' && (
        <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: '0.75rem', padding: '1.5rem', maxWidth: '700px' }}>
          <h3 style={{ fontSize: '1.15rem', fontWeight: 700, marginBottom: '1rem' }}>
            Параметры внешних интеграций
          </h3>

          <div style={{ background: '#0b1329', padding: '1rem', borderRadius: '0.5rem', border: '1px solid var(--border-color)', marginBottom: '1.5rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
              <span style={{ color: '#94a3b8' }}>Шлюз Яндекс.Расписаний:</span>
              <strong style={{ color: syncStatus?.yandex_key_configured ? '#34d399' : '#f59e0b' }}>
                {syncStatus?.yandex_key_configured ? 'Ключ подключен' : 'Демо / Fallback режим'}
              </strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
              <span style={{ color: '#94a3b8' }}>Дневной лимит запросов:</span>
              <span className="font-mono" style={{ color: '#f8fafc' }}>500 запросов/сут (кэширование в Mongo)</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: '#94a3b8' }}>Кэшированных маршрутов в БД:</span>
              <span className="font-mono" style={{ color: '#38bdf8' }}>{syncStatus?.cached_queries || 0}</span>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', marginBottom: '1rem' }}>
            <button onClick={handleSyncYandex} className="btn btn-primary">
              ⚡ Запустить синхронизацию Яндекс.Расписаний
            </button>
            <button onClick={handleSeed} className="btn btn-secondary">
              📦 Сбросить и заполнить демо-данные Коми
            </button>
          </div>

          {syncMsg && (
            <div style={{ fontSize: '0.85rem', padding: '0.75rem', borderRadius: '0.375rem', background: 'rgba(30, 41, 59, 0.7)', border: '1px solid var(--border-color)', color: syncMsg.startsWith('✓') ? '#34d399' : '#f87171' }}>
              {syncMsg}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
