import React from 'react';
import { Shield, Radio, Bell, User, Cpu } from 'lucide-react';
import { SystemHealthResponse } from '../types';

interface HeaderProps {
  health: SystemHealthResponse | null;
  loading: boolean;
}

export const Header: React.FC<HeaderProps> = ({ health, loading }) => {
  const isHealthy = health?.status === 'healthy';

  return (
    <header className="bg-sentinel-850 border-b border-sentinel-700 px-6 py-3 flex items-center justify-between shadow-md">
      <div className="flex items-center space-x-3">
        <div className="bg-sentinel-accent/20 p-2 rounded-lg border border-sentinel-accent/50 text-sentinel-accent">
          <Shield className="w-6 h-6" />
        </div>
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-xl font-bold tracking-tight text-white">SentinelX</h1>
            <span className="bg-blue-900/60 text-blue-300 text-xs px-2 py-0.5 rounded border border-blue-700 font-mono font-medium">
              GPIC 2026
            </span>
          </div>
          <p className="text-xs text-sentinel-500">Cross-Camera Vehicle Intelligence & Unified CCTV Analytics</p>
        </div>
      </div>

      <div className="flex items-center space-x-4">
        {/* Backend Connectivity Status */}
        <div className="flex items-center space-x-2 px-3 py-1.5 rounded-md bg-sentinel-800 border border-sentinel-700 text-xs">
          <Cpu className="w-4 h-4 text-slate-400" />
          <span className="text-slate-300">Backend:</span>
          {loading ? (
            <span className="text-amber-400 flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-amber-400 animate-ping" />
              Connecting...
            </span>
          ) : isHealthy ? (
            <span className="text-emerald-400 font-medium flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-400" />
              Online (v{health?.version})
            </span>
          ) : (
            <span className="text-rose-400 font-medium flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-rose-500" />
              Offline
            </span>
          )}
        </div>

        {/* Sentinel Live Sandbox Ingest Indicator */}
        <div className="flex items-center space-x-1.5 px-3 py-1.5 rounded-md bg-emerald-950/40 border border-emerald-800/60 text-emerald-400 text-xs font-medium">
          <Radio className="w-3.5 h-3.5 animate-pulse" />
          <span>Sentinel Dynamic Feed</span>
        </div>

        {/* Alerts Bell */}
        <button
          aria-label="Alerts"
          className="p-2 rounded-md hover:bg-sentinel-800 text-slate-300 hover:text-white transition-colors relative"
        >
          <Bell className="w-5 h-5" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-rose-500" />
        </button>

        {/* User Profile */}
        <div className="flex items-center space-x-2 pl-2 border-l border-sentinel-700">
          <div className="w-8 h-8 rounded-full bg-sentinel-700 flex items-center justify-center text-slate-200">
            <User className="w-4 h-4" />
          </div>
          <div className="text-left hidden md:block">
            <div className="text-xs font-semibold text-slate-200">Inspector Patel</div>
            <div className="text-[10px] text-slate-400">Gujarat Police Command</div>
          </div>
        </div>
      </div>
    </header>
  );
};
