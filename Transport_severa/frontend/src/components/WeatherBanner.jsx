import React, { useState, useEffect } from 'react';
import { api } from '../api';

export default function WeatherBanner() {
  const [weatherList, setWeatherList] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadWeather();
    const interval = setInterval(loadWeather, 60000); // 1 min refresh
    return () => clearInterval(interval);
  }, []);

  const loadWeather = async () => {
    try {
      const data = await api.getLatestWeather();
      setWeatherList(data);
    } catch (e) {
      console.error('Failed to load weather', e);
    } finally {
      setLoading(false);
    }
  };

  if (loading || weatherList.length === 0) return null;

  return (
    <div style={{ background: '#0f172a', borderBottom: '1px solid var(--border-color)', padding: '0.625rem 0', position: 'relative', zIndex: 10 }}>
      <div className="container" style={{ display: 'flex', alignItems: 'center', gap: '1rem', overflowX: 'auto', whiteSpace: 'nowrap' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.8rem', fontWeight: 600, color: '#38bdf8', paddingRight: '0.75rem', borderRight: '1px solid var(--border-color)', flexShrink: 0 }}>
          <span>🌪️</span> МЕТЕОСВОДКА РК:
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', minWidth: 0 }}>
          {weatherList.map((w, idx) => {
            const isSevere = w.alert_level === 'SEVERE';
            const isAdvisory = w.alert_level === 'ADVISORY';
            return (
              <div
                key={idx}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.6rem',
                  fontSize: '0.825rem',
                  padding: '0.25rem 0.75rem',
                  borderRadius: '0.375rem',
                  flexShrink: 0,
                  background: isSevere ? 'rgba(239, 68, 68, 0.15)' : isAdvisory ? 'rgba(245, 158, 11, 0.12)' : 'rgba(30, 41, 59, 0.7)',
                  border: `1px solid ${isSevere ? '#ef4444' : isAdvisory ? '#f59e0b' : 'var(--border-color)'}`
                }}
              >
                <span style={{ fontWeight: 600, color: '#f8fafc' }}>{w.city}:</span>
                <span className="font-mono" style={{ color: w.metrics.temperature_c <= -20 ? '#38bdf8' : '#e2e8f0' }}>
                  {w.metrics.temperature_c > 0 ? `+${w.metrics.temperature_c}` : w.metrics.temperature_c}°C
                </span>
                <span style={{ color: '#94a3b8' }}>
                  ветер {w.metrics.wind_speed_ms} м/с
                </span>
                <span style={{ fontSize: '0.75rem', color: isSevere ? '#f87171' : isAdvisory ? '#fbbf24' : '#64748b' }}>
                  {w.metrics.phenomena}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
