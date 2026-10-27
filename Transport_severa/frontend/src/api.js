// API Client for Transport Severa
function resolveApiBase() {
  const raw = import.meta.env.VITE_API_BASE_URL;
  if (!raw || String(raw).trim() === '') {
    return '/api';
  }

  let base = String(raw).trim().replace(/\/+$/, '');
  if (!/^https?:\/\//i.test(base) && !base.startsWith('/')) {
    base = `https://${base}`;
  }
  if (!base.endsWith('/api')) {
    base = `${base}/api`;
  }
  return base;
}

const API_BASE = resolveApiBase();

export const getAuthToken = () => localStorage.getItem('token');
export const setAuthToken = (token) => localStorage.setItem('token', token);
export const removeAuthToken = () => localStorage.removeItem('token');

export const getCurrentUser = () => {
  const user = localStorage.getItem('user');
  return user ? JSON.parse(user) : null;
};
export const setCurrentUser = (user) => localStorage.setItem('user', JSON.stringify(user));
export const removeCurrentUser = () => localStorage.removeItem('user');

async function request(endpoint, options = {}) {
  const token = getAuthToken();
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  };

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  if (response.status === 401) {
    removeAuthToken();
    removeCurrentUser();
  }

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Ошибка сервера' }));
    throw new Error(errorData.detail || `Ошибка ${response.status}`);
  }

  return response.json();
}

export const api = {
  // Auth
  login: async (username, password) => {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);
    const resp = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: formData,
    });
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}));
      const detail = typeof err.detail === 'string' ? err.detail : null;
      throw new Error(detail || `Ошибка входа (${resp.status})`);
    }
    const data = await resp.json();
    setAuthToken(data.access_token);
    setCurrentUser(data.user);
    return data;
  },
  getMe: () => request('/auth/me'),
  getUsers: () => request('/auth/users'),
  createUser: (userData) => request('/auth/users', { method: 'POST', body: JSON.stringify(userData) }),

  // Trips & Board
  getTrips: (params = {}) => {
    const query = new URLSearchParams(params).toString();
    return request(`/trips${query ? `?${query}` : ''}`);
  },
  getTripById: (id) => request(`/trips/${id}`),
  overrideStatus: (id, data) => request(`/trips/${id}/override-status`, { method: 'POST', body: JSON.stringify(data) }),
  hideTrip: (id, isHidden) => request(`/trips/${id}/hide`, { method: 'POST', body: JSON.stringify({ is_hidden: isHidden }) }),
  verifyTrip: (id) => request(`/trips/${id}/verify`, { method: 'POST' }),

  // Stations & Carriers
  getStations: (params = {}) => {
    const query = new URLSearchParams(params).toString();
    return request(`/stations${query ? `?${query}` : ''}`);
  },
  createStation: (data) => request('/stations', { method: 'POST', body: JSON.stringify(data) }),
  updateStation: (id, data) => request(`/stations/${encodeURIComponent(id)}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteStation: (id) => request(`/stations/${encodeURIComponent(id)}`, { method: 'DELETE' }),
  getCarriers: (transportType) => request(`/carriers${transportType ? `?transport_type=${transportType}` : ''}`),
  createCarrier: (data) => request('/carriers', { method: 'POST', body: JSON.stringify(data) }),
  updateCarrier: (id, data) => request(`/carriers/${encodeURIComponent(id)}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteCarrier: (id) => request(`/carriers/${encodeURIComponent(id)}`, { method: 'DELETE' }),

  // Weather
  getLatestWeather: (city) => request(`/weather/latest${city ? `?city=${encodeURIComponent(city)}` : ''}`),
  ingestWeather: (city, metrics) => request(`/weather/ingest?city=${encodeURIComponent(city)}`, {
    method: 'POST',
    body: JSON.stringify(metrics),
  }),

  // Subscriptions & Notifications
  subscribe: (data) => request('/subscriptions', { method: 'POST', body: JSON.stringify(data) }),
  getNotifications: (tripId) => request(`/notifications${tripId ? `?trip_id=${tripId}` : ''}`),

  // Audit & Sync
  getAuditLogs: (eventType) => request(`/audit${eventType ? `?event_type=${eventType}` : ''}`),
  getSyncStatus: () => request('/sync/status'),
  syncYandex: (fromCode, toCode) => {
    const params = new URLSearchParams();
    if (fromCode) params.set('from_code', fromCode);
    if (toCode) params.set('to_code', toCode);
    const query = params.toString();
    return request(`/sync/yandex${query ? `?${query}` : ''}`, { method: 'POST' });
  },
  seedData: () => request('/sync/seed', { method: 'POST' }),
};
