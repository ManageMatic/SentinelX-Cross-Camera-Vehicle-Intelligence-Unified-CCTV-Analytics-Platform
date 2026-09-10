import React, { useState, useMemo } from 'react';
import {
  AlertOctagon,
  ArrowRight,
  Bell,
  CheckCircle,
  CheckCircle2,
  Clock,
  Download,
  Eye,
  Filter,
  Flame,
  Radio,
  Search,
  Send,
  Shield,
  ShieldAlert,
  Sliders,
  Volume2,
  VolumeX,
  XCircle,
  Zap,
} from 'lucide-react';
import { AlertItem, AlertStatus, AlertPriority, WatchlistCategory } from '../types';
import { Button } from '../components/common/Button';
import { Card } from '../components/common/Card';
import { Modal } from '../components/common/Modal';
import { PriorityBadge, StatusBadge, CategoryBadge } from '../components/common/Badge';

interface AlertsPageProps {
  alerts: AlertItem[];
  onAcknowledgeAlert: (alertId: string) => void;
  onTrackPlate: (plate: string) => void;
}

// Fallback Demo Alerts for Gujarat Police Command Center
const defaultAlerts: AlertItem[] = [
  {
    id: 'alert-001',
    vehicle_event_id: 'evt-001',
    watchlist_entry_id: 'wl-001',
    plate_number: 'GJ01AB1234',
    watchlist_name: 'Gujarat Inter-District Gold Heist Gang',
    category: 'WANTED',
    priority: 'CRITICAL',
    camera_name: 'Ahmedabad Junction Entry Gate',
    camera_id: 'cam-ahm-01',
    location: 'Ahmedabad Junction, Ahmedabad',
    timestamp: new Date(Date.now() - 3600000 * 0.1).toISOString(),
    status: 'NEW',
    case_number: 'FIR-2026-AHM-0412',
    snapshot_url: 'https://images.unsplash.com/photo-1549399542-7e3f8b79c341?w=400',
  },
  {
    id: 'alert-002',
    vehicle_event_id: 'evt-003',
    watchlist_entry_id: 'wl-002',
    plate_number: 'GJ05CD5678',
    watchlist_name: 'Surat Diamond Corridor Hijack Alert',
    category: 'STOLEN',
    priority: 'HIGH',
    camera_name: 'Surat Ring Road Entry Flyover',
    camera_id: 'cam-sur-01',
    location: 'Ring Road, Surat',
    timestamp: new Date(Date.now() - 3600000 * 0.8).toISOString(),
    status: 'NEW',
    case_number: 'FIR-2026-SUR-1109',
    snapshot_url: 'https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?w=400',
  },
  {
    id: 'alert-003',
    vehicle_event_id: 'evt-004',
    watchlist_entry_id: 'wl-003',
    plate_number: 'GJ06XY9999',
    watchlist_name: 'Coastal Narcotics Smuggling Intercept',
    category: 'SUSPICIOUS',
    priority: 'HIGH',
    camera_name: 'Vadodara Alkapuri Underpass',
    camera_id: 'cam-vad-01',
    location: 'Alkapuri, Vadodara',
    timestamp: new Date(Date.now() - 3600000 * 2.4).toISOString(),
    status: 'ACKNOWLEDGED',
    case_number: 'FIR-2026-VAD-8841',
    acknowledged_by: 'Inspector V. Jadeja (PCR-04)',
    acknowledged_at: new Date(Date.now() - 3600000 * 2.2).toISOString(),
    snapshot_url: 'https://images.unsplash.com/photo-1503376780353-7e6692767b70?w=400',
  },
  {
    id: 'alert-004',
    vehicle_event_id: 'evt-005',
    watchlist_entry_id: 'wl-004',
    plate_number: 'GJ18GA0001',
    watchlist_name: 'State Dignitary Convoy Escort Protocol',
    category: 'VIP',
    priority: 'LOW',
    camera_name: 'Gandhinagar Secretariat Gate 1',
    camera_id: 'cam-gan-01',
    location: 'Sector 10, Gandhinagar',
    timestamp: new Date(Date.now() - 3600000 * 5.0).toISOString(),
    status: 'RESOLVED',
    case_number: 'VIP-GANDHINAGAR-01',
    acknowledged_by: 'Control Room Officer D. Solanki',
    acknowledged_at: new Date(Date.now() - 3600000 * 4.9).toISOString(),
    snapshot_url: 'https://images.unsplash.com/photo-1542282088-72c9c27ed0cd?w=400',
  },
];

export const AlertsPage: React.FC<AlertsPageProps> = ({
  alerts = [],
  onAcknowledgeAlert,
  onTrackPlate,
}) => {
  const [alertList, setAlertList] = useState<AlertItem[]>(
    alerts.length > 0 ? alerts : defaultAlerts
  );
  const [filterStatus, setFilterStatus] = useState<string>('ALL');
  const [filterPriority, setFilterPriority] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [audioAlertEnabled, setAudioAlertEnabled] = useState<boolean>(true);
  const [dispatchNotification, setDispatchNotification] = useState<string | null>(null);

  // Modal for PCR Van Interceptor Dispatch
  const [selectedDispatchAlert, setSelectedDispatchAlert] = useState<AlertItem | null>(null);
  const [selectedPcrUnit, setSelectedPcrUnit] = useState<string>('PCR-AHM-04 (Navrangpura Patrol)');

  // Filtered Alerts
  const filteredAlerts = useMemo(() => {
    return alertList.filter((a) => {
      const matchesStatus = filterStatus === 'ALL' || a.status === filterStatus;
      const matchesPriority = filterPriority === 'ALL' || a.priority === filterPriority;
      const matchesSearch =
        a.plate_number.toLowerCase().includes(searchQuery.toLowerCase()) ||
        a.watchlist_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        a.camera_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (a.case_number && a.case_number.toLowerCase().includes(searchQuery.toLowerCase()));
      return matchesStatus && matchesPriority && matchesSearch;
    });
  }, [alertList, filterStatus, filterPriority, searchQuery]);

  // Statistics
  const criticalCount = alertList.filter((a) => a.priority === 'CRITICAL' && a.status === 'NEW').length;
  const newPendingCount = alertList.filter((a) => a.status === 'NEW').length;
  const acknowledgedCount = alertList.filter((a) => a.status === 'ACKNOWLEDGED').length;

  // Local Acknowledge Action
  const handleAcknowledge = (alertId: string) => {
    setAlertList((prev) =>
      prev.map((a) =>
        a.id === alertId
          ? {
              ...a,
              status: 'ACKNOWLEDGED',
              acknowledged_by: 'Duty Officer (Command Center)',
              acknowledged_at: new Date().toISOString(),
            }
          : a
      )
    );
    if (onAcknowledgeAlert) onAcknowledgeAlert(alertId);
    setDispatchNotification(`Alert ${alertId} acknowledged and logged into immutable audit ledger.`);
    setTimeout(() => setDispatchNotification(null), 4000);
  };

  // Local Resolve Action
  const handleResolve = (alertId: string, status: AlertStatus) => {
    setAlertList((prev) =>
      prev.map((a) => (a.id === alertId ? { ...a, status } : a))
    );
    setDispatchNotification(`Alert marked as ${status}.`);
    setTimeout(() => setDispatchNotification(null), 4000);
  };

  // Simulate Instant Emergency Ingest Alert
  const handleSimulateIncomingAlert = () => {
    const randomPlates = ['GJ01ZZ8888', 'GJ27KR4321', 'GJ03MM7711'];
    const plate = randomPlates[Math.floor(Math.random() * randomPlates.length)];
    const newIncoming: AlertItem = {
      id: `alert-sim-${Date.now()}`,
      vehicle_event_id: `evt-${Date.now()}`,
      plate_number: plate,
      watchlist_name: 'CRITICAL ARMED ROBBERY HOTLIST HIT',
      category: 'WANTED',
      priority: 'CRITICAL',
      camera_name: 'SG Highway — Iscon Flyover North',
      camera_id: 'cam-ahm-02',
      location: 'SG Highway, Ahmedabad',
      timestamp: new Date().toISOString(),
      status: 'NEW',
      case_number: `FIR-2026-AHM-${Math.floor(1000 + Math.random() * 9000)}`,
      snapshot_url: 'https://images.unsplash.com/photo-1552519507-da3b142c6e3d?w=400',
    };

    setAlertList([newIncoming, ...alertList]);
    setDispatchNotification(`🚨 LIVE INCOMING HOTLIST HIT: ${plate} detected on SG Highway!`);
    setTimeout(() => setDispatchNotification(null), 5000);
  };

  // Dispatch Interceptor Confirmation
  const handleConfirmDispatch = () => {
    if (!selectedDispatchAlert) return;
    const plate = selectedDispatchAlert.plate_number;
    setSelectedDispatchAlert(null);
    setDispatchNotification(
      `🚔 DISPATCH TRANSMITTED: ${selectedPcrUnit} dispatched to intercept ${plate} at ${selectedDispatchAlert.camera_name}.`
    );
    setTimeout(() => setDispatchNotification(null), 6000);
  };

  return (
    <div className="space-y-6">
      {/* Top Dispatch Banner */}
      <div className="bg-[#180a10] p-6 rounded-2xl border border-rose-600/50 shadow-2xl flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded bg-rose-500/20 text-rose-300 font-mono text-xs font-bold border border-rose-500/40">
              REAL-TIME DISPATCH HUB
            </span>
            <span className="text-xs font-mono text-rose-400 animate-pulse flex items-center gap-1">
              <Radio className="h-3 w-3" />
              WEBSOCKET DISPATCH ACTIVE (&lt; 200MS LATENCY)
            </span>
          </div>
          <h1 className="text-xl font-black text-white font-mono tracking-wide mt-1">
            SECURITY ALERTS & HOTLIST TRIAGE
          </h1>
          <p className="text-xs text-slate-300 mt-1 font-mono">
            Statewide Gujarat multi-camera automated license plate & Re-ID cross-correlation alerts
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <Button
            variant="secondary"
            size="sm"
            onClick={() => setAudioAlertEnabled(!audioAlertEnabled)}
            icon={audioAlertEnabled ? <Volume2 className="h-3.5 w-3.5" /> : <VolumeX className="h-3.5 w-3.5" />}
          >
            {audioAlertEnabled ? 'Siren Audio ON' : 'Audio Muted'}
          </Button>

          <Button
            variant="danger"
            size="md"
            icon={<Zap className="h-4 w-4" />}
            onClick={handleSimulateIncomingAlert}
          >
            Simulate Hotlist Ingest Hit
          </Button>
        </div>
      </div>

      {dispatchNotification && (
        <div className="p-3 rounded-xl bg-rose-950/80 border border-rose-700 text-rose-200 text-xs font-mono flex items-center gap-2 animate-bounce">
          <ShieldAlert className="h-4 w-4 text-rose-400" />
          {dispatchNotification}
        </div>
      )}

      {/* KPI Severity Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-[#0c1424] p-4 rounded-xl border border-rose-900/60 shadow-lg font-mono">
          <span className="text-[10px] text-slate-400 uppercase tracking-wider block">
            Critical Action Required
          </span>
          <div className="flex items-center justify-between mt-1">
            <span className="text-2xl font-black text-rose-500">{criticalCount}</span>
            <Flame className="h-5 w-5 text-rose-500 animate-pulse" />
          </div>
          <p className="text-[10px] text-slate-500 mt-1">Immediate siren & intercept trigger</p>
        </div>

        <div className="bg-[#0c1424] p-4 rounded-xl border border-amber-900/60 shadow-lg font-mono">
          <span className="text-[10px] text-slate-400 uppercase tracking-wider block">
            Pending Officer Review
          </span>
          <div className="flex items-center justify-between mt-1">
            <span className="text-2xl font-black text-amber-400">{newPendingCount}</span>
            <Clock className="h-5 w-5 text-amber-400" />
          </div>
          <p className="text-[10px] text-slate-500 mt-1">Unacknowledged alert events</p>
        </div>

        <div className="bg-[#0c1424] p-4 rounded-xl border border-emerald-900/60 shadow-lg font-mono">
          <span className="text-[10px] text-slate-400 uppercase tracking-wider block">
            Acknowledged & Triaged
          </span>
          <div className="flex items-center justify-between mt-1">
            <span className="text-2xl font-black text-emerald-400">{acknowledgedCount}</span>
            <CheckCircle2 className="h-5 w-5 text-emerald-400" />
          </div>
          <p className="text-[10px] text-slate-500 mt-1">Audit-trailed officer actions</p>
        </div>
      </div>

      {/* Filter Tabs & Search */}
      <div className="bg-[#090e1a] p-3 rounded-xl border border-slate-800 flex flex-wrap items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-1.5 text-xs font-mono">
          {['ALL', 'NEW', 'ACKNOWLEDGED', 'RESOLVED', 'FALSE_POSITIVE'].map((st) => (
            <button
              key={st}
              onClick={() => setFilterStatus(st)}
              className={`px-3 py-1.5 rounded-lg font-bold transition-all ${
                filterStatus === st
                  ? 'bg-blue-600 text-white shadow-md shadow-blue-500/30'
                  : 'bg-[#070b14] text-slate-400 border border-slate-800 hover:text-white'
              }`}
            >
              {st === 'NEW' ? 'NEW (PENDING)' : st.replace('_', ' ')}
            </button>
          ))}
        </div>

        <div className="relative w-full sm:w-64">
          <Search className="h-3.5 w-3.5 absolute left-3 top-2.5 text-slate-400" />
          <input
            type="text"
            placeholder="Search plate, camera, case..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-[#070b14] border border-slate-800 rounded-lg pl-8 pr-3 py-1.5 text-xs text-slate-200 font-mono focus:border-blue-500 focus:outline-none"
          />
        </div>
      </div>

      {/* Alert Feed Cards */}
      <div className="space-y-4">
        {filteredAlerts.length === 0 ? (
          <div className="py-12 text-center bg-[#0c1424] rounded-2xl border border-slate-800 font-mono text-slate-400">
            <Shield className="h-8 w-8 text-slate-600 mx-auto mb-2" />
            <p className="text-sm">No alerts matching current status or query filter.</p>
          </div>
        ) : (
          filteredAlerts.map((alert) => (
            <div
              key={alert.id}
              className={`p-6 rounded-2xl border transition-all ${
                alert.status === 'NEW'
                  ? 'bg-[#120a10] border-rose-600/60 shadow-[0_0_25px_rgba(244,63,94,0.18)]'
                  : 'bg-[#0a0f1d] border-slate-800 hover:border-slate-700'
              }`}
            >
              {/* Alert Header */}
              <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 pb-4 border-b border-slate-800/80">
                <div className="flex items-center gap-3">
                  <span className="px-3.5 py-1.5 rounded-lg bg-black border-2 border-yellow-400 text-yellow-300 font-mono font-black text-lg tracking-wider shadow-md">
                    {alert.plate_number}
                  </span>
                  <PriorityBadge priority={alert.priority} />
                  <CategoryBadge category={alert.category} />
                  <StatusBadge status={alert.status} />
                </div>

                <div className="flex items-center gap-2 text-xs font-mono text-slate-400">
                  <Clock className="h-4 w-4 text-blue-400" />
                  <span>{new Date(alert.timestamp).toLocaleString()}</span>
                </div>
              </div>

              {/* Alert Body Meta */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 py-4 text-xs font-mono">
                <div>
                  <span className="text-slate-500 block text-[10px]">WATCHLIST RULE / GANG</span>
                  <span className="text-white font-bold">{alert.watchlist_name}</span>
                </div>
                <div>
                  <span className="text-slate-500 block text-[10px]">DETECTED CCTV LOCATION</span>
                  <span className="text-white font-bold">
                    {alert.camera_name} ({alert.location})
                  </span>
                </div>
                <div>
                  <span className="text-slate-500 block text-[10px]">POLICE FIR REFERENCE</span>
                  <span className="text-amber-400 font-bold">{alert.case_number || 'N/A'}</span>
                </div>
              </div>

              {/* Alert Footer Actions */}
              <div className="flex flex-wrap items-center justify-between gap-4 pt-3 border-t border-slate-800/80">
                <div className="text-[11px] font-mono text-slate-400">
                  {alert.acknowledged_by ? (
                    <span className="text-emerald-400 flex items-center gap-1">
                      <CheckCircle2 className="h-3.5 w-3.5" />
                      Acknowledged by {alert.acknowledged_by} at{' '}
                      {alert.acknowledged_at && new Date(alert.acknowledged_at).toLocaleTimeString()}
                    </span>
                  ) : (
                    <span className="text-rose-400 font-bold animate-pulse flex items-center gap-1">
                      <AlertOctagon className="h-3.5 w-3.5" />
                      PENDING IMMEDIATE OFFICER TRIAGE
                    </span>
                  )}
                </div>

                <div className="flex flex-wrap items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    icon={<Eye className="h-3.5 w-3.5" />}
                    onClick={() => onTrackPlate(alert.plate_number)}
                  >
                    Track Trajectory
                  </Button>

                  <Button
                    variant="danger"
                    size="sm"
                    icon={<Send className="h-3.5 w-3.5" />}
                    onClick={() => setSelectedDispatchAlert(alert)}
                  >
                    Dispatch PCR Van
                  </Button>

                  {alert.status === 'NEW' && (
                    <Button
                      variant="warning"
                      size="sm"
                      icon={<CheckCircle className="h-3.5 w-3.5" />}
                      onClick={() => handleAcknowledge(alert.id)}
                    >
                      Acknowledge
                    </Button>
                  )}

                  {alert.status !== 'RESOLVED' && alert.status !== 'NEW' && (
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => handleResolve(alert.id, 'RESOLVED')}
                    >
                      Mark Resolved
                    </Button>
                  )}

                  {alert.status !== 'FALSE_POSITIVE' && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleResolve(alert.id, 'FALSE_POSITIVE')}
                    >
                      False Positive
                    </Button>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Dispatch PCR Unit Confirmation Modal */}
      {selectedDispatchAlert && (
        <Modal
          isOpen={!!selectedDispatchAlert}
          onClose={() => setSelectedDispatchAlert(null)}
          title={`DISPATCH INTERCEPTOR: ${selectedDispatchAlert.plate_number}`}
          subtitle={`Target located at ${selectedDispatchAlert.camera_name}`}
          icon={<Send className="h-5 w-5 text-rose-500" />}
          maxWidth="md"
        >
          <div className="space-y-4 font-mono text-xs">
            <div className="bg-black/70 p-3 rounded-xl border border-slate-800">
              <span className="text-slate-400 block text-[10px]">SUSPECT REGISTRATION</span>
              <span className="text-xl font-bold text-yellow-300">
                {selectedDispatchAlert.plate_number}
              </span>
              <p className="text-slate-300 text-xs mt-1">
                Reason: {selectedDispatchAlert.watchlist_name} ({selectedDispatchAlert.case_number})
              </p>
            </div>

            <div>
              <label className="block text-slate-300 font-bold mb-1">
                SELECT NEAREST PATROL UNIT / PCR VAN
              </label>
              <select
                value={selectedPcrUnit}
                onChange={(e) => setSelectedPcrUnit(e.target.value)}
                className="w-full bg-[#070b14] border border-slate-700 rounded-lg p-2.5 text-white focus:outline-none focus:border-rose-500"
              >
                <option value="PCR-AHM-04 (Navrangpura Patrol)">
                  PCR-AHM-04 (Navrangpura Patrol — 1.2 KM away)
                </option>
                <option value="PCR-AHM-11 (SG Highway Rapid Action)">
                  PCR-AHM-11 (SG Highway Rapid Action — 2.8 KM away)
                </option>
                <option value="PCR-SUR-02 (Ring Road Flying Squad)">
                  PCR-SUR-02 (Ring Road Flying Squad — 0.9 KM away)
                </option>
                <option value="PCR-VAD-07 (Alkapuri Mobile Intercept)">
                  PCR-VAD-07 (Alkapuri Mobile Intercept — 1.5 KM away)
                </option>
              </select>
            </div>

            <div className="p-3 rounded-xl bg-rose-950/40 border border-rose-800/80 text-[11px] text-rose-300 space-y-1">
              <p className="font-bold">⚠️ EMERGENCY PROTOCOL WARNING:</p>
              <p>
                Dispatching will broadcast live GPS coordinates, vehicle classification, and high-res
                snapshot directly to the mobile terminal of the selected unit.
              </p>
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-800">
              <Button variant="ghost" size="sm" onClick={() => setSelectedDispatchAlert(null)}>
                Cancel
              </Button>
              <Button
                variant="danger"
                size="sm"
                icon={<Send className="h-3.5 w-3.5" />}
                onClick={handleConfirmDispatch}
              >
                Confirm Emergency Dispatch
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};
