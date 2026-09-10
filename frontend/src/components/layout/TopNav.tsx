import React, { useState, useEffect } from 'react';
import {
  Shield,
  Search,
  Bell,
  Radio,
  Clock,
  Activity,
  ChevronDown,
  Volume2,
  VolumeX,
} from 'lucide-react';
import { SystemHealthResponse, AlertItem } from '../../types';
import { StatusDot } from '../common/StatusDot';

interface TopNavProps {
  health: SystemHealthResponse | null;
  loading: boolean;
  activeAlerts: AlertItem[];
  onOpenAlerts: () => void;
  onQuickSearch: (query: string) => void;
  isAudioAlertEnabled: boolean;
  onToggleAudioAlert: () => void;
}

export const TopNav: React.FC<TopNavProps> = ({
  health,
  loading,
  activeAlerts,
  onOpenAlerts,
  onQuickSearch,
  isAudioAlertEnabled,
  onToggleAudioAlert,
}) => {
  const [time, setTime] = useState({
    ist: '',
    utc: '',
  });
  const [searchQuery, setSearchQuery] = useState('');
  const [isProfileOpen, setIsProfileOpen] = useState(false);

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setTime({
        ist: now.toLocaleTimeString('en-IN', {
          timeZone: 'Asia/Kolkata',
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit',
          hour12: false,
        }),
        utc: now.toISOString().slice(11, 19) + ' UTC',
      });
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      onQuickSearch(searchQuery.trim());
      setSearchQuery('');
    }
  };

  const criticalCount = activeAlerts.filter((a) => a.priority === 'CRITICAL' || a.priority === 'HIGH').length;

  return (
    <header className="h-16 bg-[#090e1a] border-b border-slate-800 px-4 lg:px-6 flex items-center justify-between gap-4 z-40 sticky top-0 shadow-lg">
      {/* Brand & Gujarat Police Insignia */}
      <div className="flex items-center gap-3 min-w-max">
        <div className="relative flex items-center justify-center p-1 rounded-xl bg-gradient-to-br from-amber-500/20 via-blue-950/40 to-cyan-950/50 border border-amber-500/40 shadow-[0_0_15px_rgba(245,158,11,0.25)]">
          <img
            src="/logo.png"
            alt="NETRA-X Emblem"
            className="h-8 w-8 object-contain drop-shadow-[0_0_8px_rgba(56,189,248,0.6)]"
            onError={(e) => {
              // Fallback to favicon SVG if image load fails
              e.currentTarget.src = '/favicon.svg';
            }}
          />
          <span className="absolute -top-1 -right-1 flex h-2.5 w-2.5">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
            <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500" />
          </span>
        </div>
        <div>
          <div className="flex items-center gap-2">
            <span className="text-lg font-black tracking-wider text-white font-mono bg-gradient-to-r from-amber-200 via-slate-100 to-cyan-300 bg-clip-text text-transparent">
              NETRA<span className="text-cyan-400">-X</span>
            </span>
            <span className="hidden sm:inline-block px-1.5 py-0.5 rounded bg-amber-950/80 border border-amber-600/60 text-[10px] font-bold font-mono text-amber-300 tracking-wider">
              GPIC-2026
            </span>
          </div>
          <p className="text-[10px] text-slate-400 font-medium tracking-wide flex items-center gap-1.5">
            <span>GUJARAT POLICE SURVEILLANCE COMMAND</span>
            <span className="hidden md:inline text-slate-600">•</span>
            <span className="hidden md:inline text-cyan-400 font-mono">₹0 OPEN STACK</span>
          </p>
        </div>
      </div>

      {/* Center Search Input */}
      <form
        onSubmit={handleSearchSubmit}
        className="hidden md:flex flex-1 max-w-md mx-4 relative items-center"
      >
        <div className="relative w-full">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search vehicle number (e.g. GJ01AB1234)..."
            className="w-full bg-[#0d1424] border border-slate-700/80 rounded-lg pl-10 pr-12 py-1.5 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 font-mono tracking-wider transition-all"
          />
          <Search className="h-4 w-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <span className="absolute right-2.5 top-1/2 -translate-y-1/2 text-[10px] font-mono px-1.5 py-0.5 bg-slate-800 text-slate-400 rounded border border-slate-700">
            ↵ ENTER
          </span>
        </div>
      </form>

      {/* Right Controls: Telemetry, Clock, Alerts, Profile */}
      <div className="flex items-center gap-3 lg:gap-4">
        {/* Backend Heartbeat */}
        <div className="hidden sm:flex items-center gap-2 px-2.5 py-1 rounded-lg bg-[#0d1424] border border-slate-800 text-xs">
          <StatusDot
            status={loading ? 'amber' : health?.status === 'healthy' ? 'green' : 'red'}
            size="sm"
          />
          <span className="font-mono text-[11px] text-slate-300">
            {loading ? 'CONNECTING' : health?.status === 'healthy' ? 'LIVE ENGINE' : 'OFFLINE'}
          </span>
        </div>

        {/* Tactical Clock */}
        <div className="hidden xl:flex flex-col items-end px-3 py-1 rounded-lg bg-[#0d1424] border border-slate-800 text-right">
          <div className="flex items-center gap-1 text-xs font-mono font-bold text-slate-200">
            <Clock className="h-3.5 w-3.5 text-blue-400" />
            <span>{time.ist} IST</span>
          </div>
          <span className="text-[9px] font-mono text-slate-400">{time.utc}</span>
        </div>

        {/* Audio Alert Mute/Unmute */}
        <button
          onClick={onToggleAudioAlert}
          title={isAudioAlertEnabled ? 'Emergency Siren: Enabled' : 'Emergency Siren: Muted'}
          className={`p-2 rounded-lg border transition-all ${
            isAudioAlertEnabled
              ? 'bg-blue-950/80 border-blue-700/60 text-blue-400 hover:bg-blue-900/60'
              : 'bg-slate-800/80 border-slate-700 text-slate-400 hover:bg-slate-700'
          }`}
        >
          {isAudioAlertEnabled ? <Volume2 className="h-4 w-4" /> : <VolumeX className="h-4 w-4" />}
        </button>

        {/* Active Red Alerts Button */}
        <button
          onClick={onOpenAlerts}
          className={`relative p-2 rounded-lg border transition-all flex items-center gap-2 ${
            criticalCount > 0
              ? 'bg-rose-950/90 border-rose-600/70 text-rose-300 shadow-[0_0_15px_rgba(244,63,94,0.3)] animate-pulse'
              : 'bg-[#0d1424] border-slate-800 text-slate-300 hover:border-slate-700'
          }`}
        >
          <Bell className={`h-4 w-4 ${criticalCount > 0 ? 'text-rose-400' : 'text-slate-400'}`} />
          <span className="text-xs font-mono font-bold">{activeAlerts.length}</span>
          {criticalCount > 0 && (
            <span className="absolute -top-1 -right-1 flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-3 w-3 bg-rose-500" />
            </span>
          )}
        </button>

        {/* Officer Profile */}
        <div className="relative">
          <button
            onClick={() => setIsProfileOpen(!isProfileOpen)}
            className="flex items-center gap-2 pl-2 pr-1 py-1 rounded-lg bg-[#0d1424] border border-slate-800 hover:border-slate-700 transition-all text-xs"
          >
            <div className="w-6 h-6 rounded-full bg-blue-900/80 border border-blue-500/60 flex items-center justify-center text-blue-300 font-bold text-[10px]">
              GP
            </div>
            <div className="hidden lg:block text-left">
              <p className="text-slate-200 font-semibold text-[11px] leading-tight">Insp. V. Patel</p>
              <p className="text-slate-400 text-[9px] font-mono leading-tight">HQ Control Room</p>
            </div>
            <ChevronDown className="h-3.5 w-3.5 text-slate-400" />
          </button>

          {isProfileOpen && (
            <div className="absolute right-0 mt-2 w-56 bg-[#0d1424] border border-slate-700 rounded-xl shadow-2xl p-2 z-50 animate-in fade-in zoom-in-95">
              <div className="px-3 py-2 border-b border-slate-800">
                <p className="text-xs font-bold text-white">Inspector V. Patel</p>
                <p className="text-[10px] text-slate-400 font-mono">Gujarat Police • Cyber/CCTV Wing</p>
                <p className="text-[10px] text-emerald-400 font-mono mt-0.5">Role: STATE_ADMIN</p>
              </div>
              <div className="p-1 text-xs text-slate-300">
                <div className="px-3 py-1.5 hover:bg-slate-800/80 rounded-lg cursor-pointer flex items-center gap-2">
                  <Activity className="h-3.5 w-3.5 text-blue-400" />
                  <span>Session Log</span>
                </div>
                <div className="px-3 py-1.5 hover:bg-slate-800/80 rounded-lg cursor-pointer flex items-center gap-2">
                  <Radio className="h-3.5 w-3.5 text-emerald-400" />
                  <span>Node: Sector-1 Gandhi Nagar</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
