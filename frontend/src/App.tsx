import { useState, useEffect } from 'react';
import { AppLayout } from './components/layout/AppLayout';
import { DashboardPage } from './pages/DashboardPage';
import { LiveGridPage } from './pages/LiveGridPage';
import { SearchPage } from './pages/SearchPage';
import { CorrelationPage } from './pages/CorrelationPage';
import { MapPage } from './pages/MapPage';
import { WatchlistsPage } from './pages/WatchlistsPage';
import { AlertsPage } from './pages/AlertsPage';
import { EvidencePage } from './pages/EvidencePage';
import { AuditPage } from './pages/AuditPage';
import { CamerasPage } from './pages/CamerasPage';
import { SystemPage } from './pages/SystemPage';
import { Modal } from './components/common/Modal';
import { PriorityBadge, StatusBadge, CategoryBadge } from './components/common/Badge';
import { Button } from './components/common/Button';
import {
  NavigationTab,
  SystemHealthResponse,
  SystemStatusData,
  SystemStats,
  AlertItem,
  VehicleEvent,
  Camera,
  VehicleJourney,
} from './types';
import {
  fetchSystemHealth,
  fetchSystemStatus,
  fetchSystemStats,
  DEMO_CAMERAS,
  DEMO_ALERTS,
  DEMO_VEHICLE_EVENTS,
  DEMO_WATCHLISTS,
  DEMO_EVIDENCE,
  DEMO_AUDIT_LOGS,
  DEMO_JOURNEY_GJ01AB1234,
} from './services/api';
import { CheckCircle, Eye, ShieldAlert } from 'lucide-react';

export function App() {
  const [activeTab, setActiveTab] = useState<NavigationTab>('dashboard');
  const [health, setHealth] = useState<SystemHealthResponse | null>(null);
  const [status, setStatus] = useState<SystemStatusData | null>(null);
  const [stats, setStats] = useState<SystemStats>({
    totalCameras: 12,
    onlineCameras: 11,
    offlineCameras: 1,
    activeAlerts: 3,
    detectionsToday: 18450,
    vehiclesIndexed: 4120,
    avgProcessTimeMs: 18.4,
  });
  const [loading, setLoading] = useState<boolean>(true);
  const [cameras] = useState<Camera[]>(DEMO_CAMERAS);
  const [alerts, setAlerts] = useState<AlertItem[]>(DEMO_ALERTS);
  const [events] = useState<VehicleEvent[]>(DEMO_VEHICLE_EVENTS);
  const [journey] = useState<VehicleJourney>(DEMO_JOURNEY_GJ01AB1234);
  const [selectedAlert, setSelectedAlert] = useState<AlertItem | null>(null);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [isAudioAlertEnabled, setIsAudioAlertEnabled] = useState<boolean>(true);

  useEffect(() => {
    let isMounted = true;
    const syncHealth = async () => {
      try {
        const healthData = await fetchSystemHealth();
        const statusData = await fetchSystemStatus();
        const statsData = await fetchSystemStats();
        if (isMounted) {
          setHealth(healthData);
          setStatus(statusData);
          setStats(statsData);
          setLoading(false);
        }
      } catch {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    syncHealth();
    const interval = setInterval(syncHealth, 15000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  const handleTrackPlate = (plate: string) => {
    setSearchQuery(plate);
    setActiveTab('correlation');
  };

  const handleAcknowledgeAlert = (alertId: string) => {
    setAlerts((prev) =>
      prev.map((a) =>
        a.id === alertId
          ? {
              ...a,
              status: 'ACKNOWLEDGED',
              acknowledged_by: 'Insp. V. Patel',
              acknowledged_at: new Date().toISOString(),
            }
          : a
      )
    );
    if (selectedAlert?.id === alertId) {
      setSelectedAlert((prev) =>
        prev
          ? {
              ...prev,
              status: 'ACKNOWLEDGED',
              acknowledged_by: 'Insp. V. Patel',
              acknowledged_at: new Date().toISOString(),
            }
          : null
      );
    }
  };

  return (
    <AppLayout
      activeTab={activeTab}
      onTabChange={setActiveTab}
      health={health}
      loading={loading}
      activeAlerts={alerts.filter((a) => a.status === 'NEW')}
      onSelectAlert={(alert) => setSelectedAlert(alert)}
      onQuickSearch={(query) => handleTrackPlate(query)}
      isAudioAlertEnabled={isAudioAlertEnabled}
      onToggleAudioAlert={() => setIsAudioAlertEnabled(!isAudioAlertEnabled)}
    >
      {/* Dynamic View Switching */}
      {activeTab === 'dashboard' && (
        <DashboardPage
          health={health}
          stats={stats}
          alerts={alerts.filter((a) => a.status === 'NEW')}
          recentEvents={events}
          cameras={cameras}
          onNavigate={setActiveTab}
          onSearch={handleTrackPlate}
          onSelectAlert={(alert) => setSelectedAlert(alert)}
        />
      )}

      {activeTab === 'live' && <LiveGridPage cameras={cameras} />}

      {activeTab === 'search' && (
        <SearchPage
          initialQuery={searchQuery}
          onTrackPlate={handleTrackPlate}
          events={events}
        />
      )}

      {activeTab === 'correlation' && (
        <CorrelationPage
          journey={journey}
          onOpenMap={() => setActiveTab('gis')}
          onSearchNewPlate={handleTrackPlate}
        />
      )}

      {activeTab === 'gis' && <MapPage cameras={cameras} journey={journey} />}

      {activeTab === 'watchlists' && <WatchlistsPage watchlists={DEMO_WATCHLISTS} />}

      {activeTab === 'alerts' && (
        <AlertsPage
          alerts={alerts}
          onAcknowledgeAlert={handleAcknowledgeAlert}
          onTrackPlate={handleTrackPlate}
        />
      )}

      {activeTab === 'evidence' && <EvidencePage evidence={DEMO_EVIDENCE} />}

      {activeTab === 'audit' && <AuditPage logs={DEMO_AUDIT_LOGS} />}

      {activeTab === 'cameras' && <CamerasPage cameras={cameras} />}

      {activeTab === 'system' && <SystemPage status={status} health={health} />}

      {/* Real-time Alert Triage Modal */}
      {selectedAlert && (
        <Modal
          isOpen={!!selectedAlert}
          onClose={() => setSelectedAlert(null)}
          title={`ALERT TRIAGE: ${selectedAlert.plate_number}`}
          subtitle={`Triggered on ${selectedAlert.camera_name} • ${new Date(
            selectedAlert.timestamp
          ).toLocaleString()}`}
          icon={<ShieldAlert className="h-5 w-5 text-rose-500" />}
          maxWidth="2xl"
          footer={
            <>
              <Button variant="ghost" size="sm" onClick={() => setSelectedAlert(null)}>
                Dismiss View
              </Button>
              <Button
                variant="outline"
                size="sm"
                icon={<Eye className="h-3.5 w-3.5" />}
                onClick={() => {
                  setSelectedAlert(null);
                  handleTrackPlate(selectedAlert.plate_number);
                }}
              >
                Track Cross-Camera Movement
              </Button>
              {selectedAlert.status === 'NEW' && (
                <Button
                  variant="warning"
                  size="sm"
                  icon={<CheckCircle className="h-3.5 w-3.5" />}
                  onClick={() => handleAcknowledgeAlert(selectedAlert.id)}
                >
                  Acknowledge Alert
                </Button>
              )}
            </>
          }
        >
          <div className="space-y-4 font-mono text-xs">
            <div className="flex items-center justify-between bg-black/60 p-3 rounded-xl border border-slate-800">
              <span className="text-xl font-bold text-yellow-300">
                {selectedAlert.plate_number}
              </span>
              <div className="flex items-center gap-2">
                <PriorityBadge priority={selectedAlert.priority} />
                <CategoryBadge category={selectedAlert.category} />
                <StatusBadge status={selectedAlert.status} />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4 p-4 rounded-xl bg-[#090e1a] border border-slate-800">
              <div>
                <span className="text-slate-400 block text-[10px]">WATCHLIST RULE</span>
                <span className="text-white font-bold">{selectedAlert.watchlist_name}</span>
              </div>
              <div>
                <span className="text-slate-400 block text-[10px]">CASE NUMBER</span>
                <span className="text-amber-400 font-bold">
                  {selectedAlert.case_number || 'ACTIVE_ALERT'}
                </span>
              </div>
              <div>
                <span className="text-slate-400 block text-[10px]">CCTV NODE</span>
                <span className="text-white font-bold">{selectedAlert.camera_name}</span>
              </div>
              <div>
                <span className="text-slate-400 block text-[10px]">LOCATION</span>
                <span className="text-white font-bold">{selectedAlert.location}</span>
              </div>
            </div>

            <div className="p-3 rounded-xl bg-blue-950/40 border border-blue-800/60 text-blue-200 text-[11px]">
              ℹ️ Automated alert dispatched over WebSocket channel in &lt; 500ms. Chain of custody
              snapshot cryptographically indexed with SHA-256 seal.
            </div>
          </div>
        </Modal>
      )}
    </AppLayout>
  );
}

export default App;
