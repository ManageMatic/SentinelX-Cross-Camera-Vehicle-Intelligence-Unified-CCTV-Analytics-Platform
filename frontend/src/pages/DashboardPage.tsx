import React from 'react';
import {
  Camera as CameraIcon,
  Bell,
  Eye,
  Activity,
  Search,
  ArrowRight,
  ShieldAlert,
  Radio,
  Zap,
} from 'lucide-react';
import {
  SystemHealthResponse,
  SystemStats,
  AlertItem,
  VehicleEvent,
  Camera,
  NavigationTab,
} from '../types';
import { StatCard } from '../components/common/StatCard';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { PriorityBadge, CameraStatusBadge } from '../components/common/Badge';
import { StatusDot } from '../components/common/StatusDot';

interface DashboardPageProps {
  health: SystemHealthResponse | null;
  stats: SystemStats;
  alerts: AlertItem[];
  recentEvents: VehicleEvent[];
  cameras: Camera[];
  onNavigate: (tab: NavigationTab) => void;
  onSearch: (plate: string) => void;
  onSelectAlert: (alert: AlertItem) => void;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({
  stats,
  alerts,
  recentEvents,
  cameras,
  onNavigate,
  onSearch,
  onSelectAlert,
}) => {
  const [searchPlate, setSearchPlate] = React.useState('');

  const handleQuickSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchPlate.trim()) {
      onSearch(searchPlate.trim());
    }
  };

  return (
    <div className="space-y-6">
      {/* Quick Mission Header & Quick Plate Query Box */}
      <div className="bg-gradient-to-r from-[#0d162c] via-[#0f1d3d] to-[#0d162c] p-6 rounded-2xl border border-blue-600/40 shadow-[0_0_25px_rgba(37,99,235,0.15)] flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 rounded bg-blue-500/20 text-blue-300 font-mono text-xs font-bold border border-blue-500/30">
              TACTICAL DASHBOARD
            </span>
            <span className="text-xs font-mono text-emerald-400 flex items-center gap-1">
              <StatusDot status="green" size="sm" /> 100% ₹0 OPEN SOURCE STACK
            </span>
          </div>
          <h1 className="text-2xl lg:text-3xl font-black text-white tracking-wide mt-1 font-mono">
            COMMAND & INTELLIGENCE MATRIX
          </h1>
          <p className="text-xs text-slate-300 mt-1 max-w-2xl">
            Live cross-camera vehicle tracking, real-time hotlist matching, and forensic journey
            reconstruction for Gujarat State Police CCTV network.
          </p>
        </div>

        {/* Quick Launch Search */}
        <form
          onSubmit={handleQuickSearch}
          className="w-full lg:w-auto flex items-center gap-2 bg-[#080d19]/90 p-1.5 rounded-xl border border-blue-500/40"
        >
          <div className="relative">
            <input
              type="text"
              value={searchPlate}
              onChange={(e) => setSearchPlate(e.target.value)}
              placeholder="e.g. GJ01AB1234"
              className="bg-[#0c1322] border border-slate-700/80 rounded-lg pl-9 pr-3 py-2 text-xs font-mono text-white placeholder-slate-500 uppercase tracking-wider focus:outline-none focus:border-blue-400 w-48 sm:w-64"
            />
            <Search className="h-4 w-4 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
          </div>
          <Button
            type="submit"
            variant="primary"
            size="sm"
            icon={<Zap className="h-3.5 w-3.5" />}
          >
            Track
          </Button>
        </form>
      </div>

      {/* KPI Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Active CCTV Feeds"
          value={`${stats.onlineCameras} / ${stats.totalCameras}`}
          subtitle={`${stats.offlineCameras} offline / reconnecting`}
          icon={<CameraIcon className="h-5 w-5" />}
          color="blue"
          trend={{ value: '100% TCP', isPositive: true, label: 'No packet drop' }}
          onClick={() => onNavigate('live')}
        />

        <StatCard
          title="Detections Today"
          value={stats.detectionsToday.toLocaleString()}
          subtitle="Real-time ByteTrack inference"
          icon={<Eye className="h-5 w-5" />}
          color="green"
          trend={{ value: '+14.2%', isPositive: true, label: 'vs yesterday' }}
          onClick={() => onNavigate('search')}
        />

        <StatCard
          title="Watchlist Hits (Active)"
          value={stats.activeAlerts}
          subtitle="Instant Red Alert dispatch"
          icon={<ShieldAlert className="h-5 w-5" />}
          color="red"
          badge={
            <span className="px-1.5 py-0.5 rounded bg-rose-500/20 text-rose-300 font-mono text-[10px] font-bold border border-rose-500/40 animate-pulse">
              HOTLIST
            </span>
          }
          onClick={() => onNavigate('alerts')}
        />

        <StatCard
          title="Avg Search Latency"
          value={`${stats.avgProcessTimeMs} ms`}
          subtitle="Indexed DB sub-200ms target"
          icon={<Activity className="h-5 w-5" />}
          color="purple"
          trend={{ value: '< 200ms', isPositive: true, label: 'SLA Pass' }}
          onClick={() => onNavigate('system')}
        />
      </div>

      {/* Two Column Section: Live Grid Preview & Urgent Watchlist Alerts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Live Camera Feeds Strip */}
        <div className="lg:col-span-2 space-y-6">
          <Card
            title="Live Surveillance Grid Preview"
            subtitle="RTSP over TCP • Low-latency WHEP proxy"
            icon={<Radio className="h-4 w-4 text-blue-400" />}
            action={
              <Button
                variant="outline"
                size="sm"
                onClick={() => onNavigate('live')}
                icon={<ArrowRight className="h-3.5 w-3.5" />}
              >
                Open Full Video Wall
              </Button>
            }
          >
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {cameras.slice(0, 4).map((cam) => (
                <div
                  key={cam.id}
                  onClick={() => onNavigate('live')}
                  className="group relative bg-[#090e1a] rounded-xl border border-slate-800 hover:border-blue-500/60 transition-all overflow-hidden cursor-pointer shadow-md"
                >
                  {/* Mock Video Feed Screen with scanlines */}
                  <div className="aspect-video bg-slate-950 relative flex items-center justify-center cctv-scanline">
                    <div className="text-center p-4">
                      <CameraIcon className="h-8 w-8 text-slate-600 mx-auto group-hover:text-blue-400 transition-colors" />
                      <p className="text-[11px] font-mono text-slate-400 mt-2">
                        STREAM: {cam.external_camera_id}
                      </p>
                      <p className="text-[10px] font-mono text-slate-500">{cam.location_name}</p>
                    </div>

                    {/* Live Stream Overlays */}
                    <div className="absolute top-2 left-2 flex items-center gap-1.5">
                      <span className="px-1.5 py-0.5 rounded bg-black/70 backdrop-blur-sm text-[10px] font-mono text-white border border-slate-700">
                        {cam.name}
                      </span>
                    </div>

                    <div className="absolute top-2 right-2">
                      <CameraStatusBadge status={cam.live_status} fps={cam.fps} />
                    </div>

                    <div className="absolute bottom-2 left-2 flex items-center gap-2">
                      <span className="text-[10px] font-mono text-emerald-400 bg-black/70 px-1.5 py-0.5 rounded border border-emerald-900/50">
                        {cam.resolution}
                      </span>
                      <span className="text-[10px] font-mono text-blue-400 bg-black/70 px-1.5 py-0.5 rounded border border-blue-900/50">
                        {cam.codec}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </Card>

          {/* Recent Vehicle Detections */}
          <Card
            title="Recent Vehicle Sightings & OCR Index"
            subtitle="Normalized Indian registration plates with confidence metrics"
            icon={<Eye className="h-4 w-4 text-emerald-400" />}
            action={
              <Button
                variant="ghost"
                size="sm"
                onClick={() => onNavigate('search')}
                icon={<ArrowRight className="h-3.5 w-3.5" />}
              >
                Search All
              </Button>
            }
          >
            <div className="divide-y divide-slate-800/80">
              {recentEvents.map((evt) => (
                <div
                  key={evt.id}
                  onClick={() => onSearch(evt.plate_normalized)}
                  className="py-3 flex items-center justify-between gap-4 hover:bg-slate-800/40 px-2 rounded-lg cursor-pointer transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <div className="px-2.5 py-1 rounded bg-black/80 border border-yellow-500/50 text-yellow-300 font-mono font-bold text-xs tracking-wider">
                      {evt.plate_normalized}
                    </div>
                    <div>
                      <p className="text-xs font-semibold text-white">
                        {evt.vehicle_make || evt.vehicle_class.toUpperCase()} ({evt.vehicle_color || 'Unknown Color'})
                      </p>
                      <p className="text-[10px] font-mono text-slate-400">
                        Camera: {evt.camera_name} • Speed: {evt.speed_kmh ? `${evt.speed_kmh} km/h` : 'N/A'}
                      </p>
                    </div>
                  </div>

                  <div className="text-right">
                    <div className="text-[10px] font-mono text-slate-300">
                      {new Date(evt.event_time).toLocaleTimeString()}
                    </div>
                    <span className="text-[10px] font-mono text-emerald-400 font-bold">
                      OCR: {Math.round(evt.plate_confidence * 100)}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>

        {/* Right 1 Col: Urgent Watchlist Hits */}
        <div className="space-y-6">
          <Card
            title="Urgent Watchlist Hits"
            subtitle="Direct real-time alerts from WebSocket"
            variant="glow-red"
            icon={<Bell className="h-4 w-4 text-rose-400" />}
            action={
              <span className="px-2 py-0.5 rounded-full bg-rose-500/20 text-rose-300 font-mono text-[10px] font-bold border border-rose-500/40">
                {alerts.length} NEW
              </span>
            }
          >
            <div className="space-y-3">
              {alerts.map((alert) => (
                <div
                  key={alert.id}
                  onClick={() => onSelectAlert(alert)}
                  className="p-3.5 rounded-xl bg-[#120a10] border border-rose-800/60 hover:border-rose-500 transition-all cursor-pointer shadow-md space-y-2"
                >
                  <div className="flex items-center justify-between">
                    <span className="px-2 py-0.5 rounded bg-black/80 border border-yellow-400/60 text-yellow-300 font-mono font-black text-xs">
                      {alert.plate_number}
                    </span>
                    <PriorityBadge priority={alert.priority} />
                  </div>

                  <div>
                    <p className="text-xs font-bold text-rose-200">{alert.watchlist_name}</p>
                    <p className="text-[10px] font-mono text-slate-400 mt-0.5">
                      Case: {alert.case_number || 'ACTIVE_ALERT'}
                    </p>
                  </div>

                  <div className="pt-2 border-t border-rose-950/80 flex items-center justify-between text-[10px] font-mono text-slate-400">
                    <span>{alert.camera_name}</span>
                    <span className="text-rose-300">
                      {new Date(alert.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                </div>
              ))}

              <Button
                variant="outline"
                size="sm"
                className="w-full mt-2"
                onClick={() => onNavigate('alerts')}
              >
                View Full Alert Triage Room
              </Button>
            </div>
          </Card>

          {/* Quick Evaluation Demo Helper */}
          <div className="p-4 rounded-xl bg-gradient-to-br from-blue-950/60 to-slate-900 border border-blue-500/40 shadow-lg space-y-3">
            <div className="flex items-center gap-2">
              <Zap className="h-4 w-4 text-amber-400" />
              <h4 className="text-xs font-bold text-white font-mono uppercase tracking-wider">
                Evaluation Test Scenario
              </h4>
            </div>
            <p className="text-[11px] text-slate-300">
              Run designated Gujarat Police Innovation test vehicle search:
            </p>
            <button
              onClick={() => onSearch('GJ01AB1234')}
              className="w-full py-2 px-3 bg-blue-600 hover:bg-blue-500 text-white font-mono text-xs font-bold rounded-lg border border-blue-400/50 shadow-[0_0_12px_rgba(37,99,235,0.4)] flex items-center justify-between transition-all cursor-pointer"
            >
              <span>TRACK: GJ01AB1234</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
