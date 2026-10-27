import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import WeatherBanner from './components/WeatherBanner';
import Board from './components/Board';
import DispatcherPanel from './components/DispatcherPanel';
import AdminPanel from './components/AdminPanel';
import TripModal from './components/TripModal';
import SubscribeModal from './components/SubscribeModal';
import LoginModal from './components/LoginModal';
import { getCurrentUser, removeAuthToken, removeCurrentUser } from './api';

export default function App() {
  const [activeTab, setActiveTab] = useState('board'); // 'board' | 'dispatcher' | 'admin'
  const [currentUser, setCurrentUser] = useState(null);
  const [isLoginOpen, setIsLoginOpen] = useState(false);
  const [selectedTrip, setSelectedTrip] = useState(null);
  const [subscribingTrip, setSubscribingTrip] = useState(null);

  useEffect(() => {
    const user = getCurrentUser();
    if (user) {
      setCurrentUser(user);
    }
  }, []);

  const handleLoginSuccess = (user) => {
    setCurrentUser(user);
    if (user.role === 'DISPATCHER') {
      setActiveTab('dispatcher');
    } else if (user.role === 'ADMIN') {
      setActiveTab('admin');
    }
  };

  const handleLogout = () => {
    removeAuthToken();
    removeCurrentUser();
    setCurrentUser(null);
    setActiveTab('board');
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Navigation Bar */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        currentUser={currentUser}
        onOpenLogin={() => setIsLoginOpen(true)}
        onLogout={handleLogout}
      />

      {/* Extreme Northern Weather Live Banner */}
      <WeatherBanner />

      {/* Main Content Area */}
      <main style={{ flex: 1 }}>
        {activeTab === 'board' && (
          <Board
            onSelectTrip={(t) => setSelectedTrip(t)}
            onSubscribeTrip={(t) => setSubscribingTrip(t)}
          />
        )}

        {activeTab === 'dispatcher' && (
          <DispatcherPanel />
        )}

        {activeTab === 'admin' && (
          <AdminPanel />
        )}
      </main>

      {/* Footer */}
      <footer style={{ background: 'var(--bg-header)', borderTop: '1px solid var(--border-color)', padding: '1.5rem 0', marginTop: 'auto' }}>
        <div className="container" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem', fontSize: '0.8rem', color: '#64748b' }}>
          <div>
            © 2026 Онлайн-табло «Транспорт Севера» (Республика Коми). Сыктывкар — Ухта — Усинск — Печора.
          </div>
          <div style={{ display: 'flex', gap: '1rem' }}>
            <span>Интеграция: API Яндекс.Расписаний v3</span>
            <span>•</span>
            <span>Метеомониторинг Севера</span>
          </div>
        </div>
      </footer>

      {/* Modals */}
      {selectedTrip && (
        <TripModal
          trip={selectedTrip}
          onClose={() => setSelectedTrip(null)}
          onSubscribe={(t) => setSubscribingTrip(t)}
        />
      )}

      {subscribingTrip && (
        <SubscribeModal
          trip={subscribingTrip}
          onClose={() => setSubscribingTrip(null)}
        />
      )}

      {isLoginOpen && (
        <LoginModal
          onClose={() => setIsLoginOpen(false)}
          onSuccess={handleLoginSuccess}
        />
      )}
    </div>
  );
}
