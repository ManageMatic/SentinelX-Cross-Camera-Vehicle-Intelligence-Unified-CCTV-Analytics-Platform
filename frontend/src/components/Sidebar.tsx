import React from 'react';
import {
  LayoutDashboard,
  Camera,
  Tv,
  Search,
  Route,
  ListOrdered,
  AlertTriangle,
  Map,
  FileCheck,
  History,
  Activity,
} from 'lucide-react';
import { NavigationTab } from '../types';

interface SidebarProps {
  activeTab: NavigationTab;
  onTabChange: (tab: NavigationTab) => void;
}

interface NavItem {
  id: NavigationTab;
  label: string;
  icon: React.ElementType;
  badge?: string;
}

const NAV_ITEMS: NavItem[] = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'cameras', label: 'Camera Registry', icon: Camera },
  { id: 'live', label: 'Live Monitoring', icon: Tv },
  { id: 'search', label: 'Vehicle Search', icon: Search },
  { id: 'investigation', label: 'Investigation & Re-ID', icon: Route },
  { id: 'gis', label: 'GIS Map', icon: Map },
  { id: 'watchlist', label: 'Watchlist', icon: ListOrdered },
  { id: 'alerts', label: 'Live Alerts', icon: AlertTriangle, badge: 'LIVE' },
  { id: 'evidence', label: 'Evidence Vault', icon: FileCheck },
  { id: 'audit', label: 'Audit Logs', icon: History },
  { id: 'health', label: 'System Health', icon: Activity },
];

export const Sidebar: React.FC<SidebarProps> = ({ activeTab, onTabChange }) => {
  return (
    <aside className="w-64 bg-sentinel-850 border-r border-sentinel-700 flex flex-col justify-between select-none">
      <div className="py-4 px-3 space-y-1">
        <div className="px-3 pb-2 text-[10px] font-bold uppercase tracking-wider text-slate-400">
          Intelligence & Operations
        </div>
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onTabChange(item.id)}
              className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                isActive
                  ? 'bg-sentinel-accent text-white shadow-sm'
                  : 'text-slate-300 hover:bg-sentinel-800 hover:text-white'
              }`}
            >
              <div className="flex items-center space-x-3">
                <Icon className={`w-4 h-4 ${isActive ? 'text-white' : 'text-slate-400'}`} />
                <span>{item.label}</span>
              </div>
              {item.badge && (
                <span className="text-[10px] uppercase font-bold px-1.5 py-0.5 rounded bg-rose-500/20 text-rose-300 border border-rose-500/40">
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </div>

      <div className="p-4 border-t border-sentinel-700 text-xs text-slate-400">
        <div className="flex items-center justify-between">
          <span>Target Architecture</span>
          <span className="text-emerald-400 font-mono">80k Ready</span>
        </div>
        <div className="mt-1 text-[11px] text-slate-500">Zero-Cost Free OSS Stack</div>
      </div>
    </aside>
  );
};
