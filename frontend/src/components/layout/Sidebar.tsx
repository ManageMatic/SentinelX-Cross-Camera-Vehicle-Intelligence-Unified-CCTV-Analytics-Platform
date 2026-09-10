import React, { useState } from 'react';
import {
  LayoutDashboard,
  Grid,
  Search,
  GitFork,
  MapPin,
  ListOrdered,
  BellRing,
  ShieldCheck,
  FileText,
  Camera,
  Cpu,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import { NavigationTab } from '../../types';

interface SidebarProps {
  activeTab: NavigationTab;
  onTabChange: (tab: NavigationTab) => void;
  activeAlertCount?: number;
}

interface NavItem {
  id: NavigationTab;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: string | number;
  badgeColor?: 'red' | 'blue' | 'amber';
}

interface NavGroup {
  title: string;
  items: NavItem[];
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  onTabChange,
  activeAlertCount = 0,
}) => {
  const [collapsed, setCollapsed] = useState(false);

  const navGroups: NavGroup[] = [
    {
      title: 'LIVE SURVEILLANCE',
      items: [
        { id: 'dashboard', label: 'Overview', icon: LayoutDashboard },
        { id: 'live', label: 'Live CCTV Grid', icon: Grid },
        { id: 'gis', label: 'GIS Tactical Map', icon: MapPin },
        { id: 'cameras', label: 'Camera Registry', icon: Camera },
      ],
    },
    {
      title: 'VEHICLE INTELLIGENCE',
      items: [
        { id: 'search', label: 'Plate Search', icon: Search },
        { id: 'correlation', label: 'Cross-Camera Re-ID', icon: GitFork },
      ],
    },
    {
      title: 'SECURITY & ALERTS',
      items: [
        { id: 'watchlists', label: 'Hotlists / Watchlists', icon: ListOrdered },
        {
          id: 'alerts',
          label: 'Real-Time Alerts',
          icon: BellRing,
          badge: activeAlertCount > 0 ? activeAlertCount : undefined,
          badgeColor: 'red',
        },
      ],
    },
    {
      title: 'FORENSICS & SYSTEM',
      items: [
        { id: 'evidence', label: 'Evidence Vault (SHA-256)', icon: ShieldCheck },
        { id: 'audit', label: 'Immutable Audit Logs', icon: FileText },
        { id: 'system', label: 'System Diagnostics', icon: Cpu },
      ],
    },
  ];

  return (
    <aside
      className={`bg-[#070b14] border-r border-slate-800 transition-all duration-300 flex flex-col justify-between select-none z-30 ${
        collapsed ? 'w-16' : 'w-64'
      }`}
    >
      {/* Navigation Group Items */}
      <div className="p-3 space-y-5 overflow-y-auto flex-1">
        {navGroups.map((group) => (
          <div key={group.title} className="space-y-1">
            {!collapsed && (
              <p className="px-3 text-[10px] font-mono font-bold uppercase tracking-wider text-slate-400">
                {group.title}
              </p>
            )}
            <div className="space-y-0.5">
              {group.items.map((item) => {
                const Icon = item.icon;
                const isActive = activeTab === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => onTabChange(item.id)}
                    title={collapsed ? item.label : undefined}
                    className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-xs font-medium transition-all duration-150 cursor-pointer ${
                      isActive
                        ? 'bg-blue-600/20 text-blue-300 border border-blue-500/50 shadow-[0_0_12px_rgba(37,99,235,0.2)] font-semibold'
                        : 'text-slate-400 hover:text-slate-100 hover:bg-slate-800/60 border border-transparent'
                    }`}
                  >
                    <Icon
                      className={`h-4 w-4 flex-shrink-0 ${
                        isActive ? 'text-blue-400' : 'text-slate-400 group-hover:text-slate-200'
                      }`}
                    />
                    {!collapsed && (
                      <span className="truncate text-left flex-1">{item.label}</span>
                    )}
                    {!collapsed && item.badge !== undefined && (
                      <span
                        className={`text-[10px] font-mono font-bold px-1.5 py-0.5 rounded-full ${
                          item.badgeColor === 'red'
                            ? 'bg-rose-500/30 text-rose-300 border border-rose-500/50'
                            : 'bg-blue-500/30 text-blue-300 border border-blue-500/50'
                        }`}
                      >
                        {item.badge}
                      </span>
                    )}
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      {/* Collapse Toggle Footer */}
      <div className="p-3 border-t border-slate-800/80 bg-[#060911] flex items-center justify-between">
        {!collapsed && (
          <div className="text-[10px] font-mono text-slate-400">
            <span>SentinelX Core v1.0</span>
          </div>
        )}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors mx-auto"
          title={collapsed ? 'Expand Sidebar' : 'Collapse Sidebar'}
        >
          {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
        </button>
      </div>
    </aside>
  );
};
