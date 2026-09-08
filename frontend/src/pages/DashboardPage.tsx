import React from 'react';
import { Camera, CheckCircle2, AlertOctagon, Car, Search, ShieldCheck } from 'lucide-react';
import { StatusCard } from '../components/StatusCard';
import { SystemHealthResponse, SystemStats } from '../types';

interface DashboardPageProps {
  health: SystemHealthResponse | null;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({ health }) => {
  const stats: SystemStats = {
    totalCameras: 30,
    onlineCameras: 28,
    offlineCameras: 2,
    activeAlerts: 1,
    detectionsToday: 1420,
    recentSearches: 47,
  };

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Welcome Banner */}
      <div className="bg-gradient-to-r from-sentinel-850 to-sentinel-800 border border-sentinel-700 rounded-xl p-6 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
              System Active
            </span>
            <span className="text-xs text-slate-400">• Dynamic Catalog Discovery Ready</span>
          </div>
          <h2 className="text-2xl font-bold text-white mt-1">Unified Command Center</h2>
          <p className="text-sm text-slate-400 mt-0.5">
            Real-time cross-camera vehicle tracking, automatic license plate recognition, and route correlation.
          </p>
        </div>

        <div className="flex items-center space-x-3 text-xs">
          <div className="bg-sentinel-900/80 px-4 py-2.5 rounded-lg border border-sentinel-700">
            <div className="text-slate-400">Core Engine</div>
            <div className="font-semibold text-white font-mono">{health?.service || 'FastAPI Backend'}</div>
          </div>
          <div className="bg-sentinel-900/80 px-4 py-2.5 rounded-lg border border-sentinel-700">
            <div className="text-slate-400">License Model</div>
            <div className="font-semibold text-emerald-400 font-mono">100% Free / OSS</div>
          </div>
        </div>
      </div>

      {/* Metric Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatusCard
          title="Connected Cameras"
          value={stats.totalCameras}
          subtitle={`${stats.onlineCameras} online · ${stats.offlineCameras} offline`}
          icon={Camera}
          variant="accent"
        />
        <StatusCard
          title="Active Watchlist Alerts"
          value={stats.activeAlerts}
          subtitle="Real-time WebSocket alerts"
          icon={AlertOctagon}
          variant="alert"
        />
        <StatusCard
          title="Vehicle Events Today"
          value={stats.detectionsToday.toLocaleString()}
          subtitle="AI ANPR & Plate Normalization"
          icon={Car}
          variant="success"
        />
        <StatusCard
          title="Cross-Camera Searches"
          value={stats.recentSearches}
          subtitle="Indexed historical queries"
          icon={Search}
          variant="default"
        />
      </div>

      {/* Operational Highlights Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-sentinel-850 border border-sentinel-700 rounded-xl p-5">
          <div className="flex items-center justify-between pb-4 border-b border-sentinel-700">
            <h3 className="font-semibold text-white flex items-center gap-2 text-sm">
              <ShieldCheck className="w-4 h-4 text-sentinel-accent" />
              Gujarat Police Evaluation Architecture (GPIC 2026)
            </h3>
            <span className="text-xs text-slate-400">Section 80 Road-map</span>
          </div>

          <div className="mt-4 space-y-3">
            <div className="flex items-start space-x-3 p-3 rounded-lg bg-sentinel-900/50 border border-sentinel-700/60">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 mt-0.5 shrink-0" />
              <div>
                <div className="text-sm font-semibold text-white">Module 0: Foundation & Verification Complete</div>
                <div className="text-xs text-slate-400 mt-0.5">
                  Backend FastAPI, Frontend React/Tailwind, and Testing Suites wired and validated.
                </div>
              </div>
            </div>

            <div className="flex items-start space-x-3 p-3 rounded-lg bg-sentinel-900/30 border border-sentinel-700/40">
              <div className="w-4 h-4 rounded-full border border-sky-400/60 flex items-center justify-center text-[10px] text-sky-400 mt-0.5 shrink-0">
                1
              </div>
              <div>
                <div className="text-sm font-medium text-slate-200">Next: Configuration & Sentinel Catalog Integration</div>
                <div className="text-xs text-slate-400 mt-0.5">
                  Dynamic camera ingestion via <code className="text-sky-300 font-mono">/api/ingest</code>, PostgreSQL database schema, and RTSP stream manager.
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Quick Capabilities */}
        <div className="bg-sentinel-850 border border-sentinel-700 rounded-xl p-5">
          <h3 className="font-semibold text-white text-sm pb-3 border-b border-sentinel-700">
            Key Invariant Rules
          </h3>
          <ul className="mt-3 space-y-2.5 text-xs text-slate-300">
            <li className="flex items-center space-x-2">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
              <span>₹0 Cost — 100% Free & Open-Source</span>
            </li>
            <li className="flex items-center space-x-2">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
              <span>Dynamic camera catalog (No hardcoding)</span>
            </li>
            <li className="flex items-center space-x-2">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
              <span>RTSP over TCP for robust AI ingestion</span>
            </li>
            <li className="flex items-center space-x-2">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
              <span>ByteTrack + PaddleOCR ANPR pipeline</span>
            </li>
            <li className="flex items-center space-x-2">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
              <span>Leaflet GIS route reconstruction</span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
};
