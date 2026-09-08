import { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { Sidebar } from './components/Sidebar';
import { DashboardPage } from './pages/DashboardPage';
import { fetchSystemHealth } from './services/api';
import { NavigationTab, SystemHealthResponse } from './types';

export function App() {
  const [activeTab, setActiveTab] = useState<NavigationTab>('dashboard');
  const [health, setHealth] = useState<SystemHealthResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    let isMounted = true;
    const checkHealth = async () => {
      try {
        const data = await fetchSystemHealth();
        if (isMounted) {
          setHealth(data);
          setLoading(false);
        }
      } catch (err) {
        if (isMounted) {
          // Keep health null if unreachable
          setLoading(false);
        }
      }
    };

    checkHealth();
    const interval = setInterval(checkHealth, 15000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  return (
    <div className="min-h-screen flex flex-col bg-sentinel-900 text-slate-100">
      <Header health={health} loading={loading} />
      <div className="flex-1 flex overflow-hidden">
        <Sidebar activeTab={activeTab} onTabChange={setActiveTab} />
        <main className="flex-1 overflow-y-auto bg-sentinel-900">
          {activeTab === 'dashboard' && <DashboardPage health={health} />}
          {activeTab !== 'dashboard' && (
            <div className="p-8 max-w-4xl mx-auto">
              <div className="bg-sentinel-850 border border-sentinel-700 rounded-xl p-8 text-center">
                <h3 className="text-xl font-bold text-white capitalize">
                  {activeTab.replace('-', ' ')} Module
                </h3>
                <p className="text-sm text-slate-400 mt-2">
                  This module is scheduled for implementation in upcoming phases per Section 80 specification.
                </p>
                <div className="mt-6">
                  <button
                    onClick={() => setActiveTab('dashboard')}
                    className="px-4 py-2 bg-sentinel-accent text-white text-sm font-semibold rounded-lg hover:bg-sky-500 transition-colors"
                  >
                    Return to Dashboard
                  </button>
                </div>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

export default App;
