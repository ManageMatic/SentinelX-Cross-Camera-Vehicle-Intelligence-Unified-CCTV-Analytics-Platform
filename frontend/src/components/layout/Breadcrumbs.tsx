import React from 'react';
import { ChevronRight, Home } from 'lucide-react';
import { NavigationTab } from '../../types';

interface BreadcrumbsProps {
  activeTab: NavigationTab;
  onTabChange: (tab: NavigationTab) => void;
  subTitle?: string;
}

export const Breadcrumbs: React.FC<BreadcrumbsProps> = ({
  activeTab,
  onTabChange,
  subTitle,
}) => {
  const tabTitles: Record<NavigationTab, { group: string; label: string }> = {
    dashboard: { group: 'Live Surveillance', label: 'Command Overview' },
    live: { group: 'Live Surveillance', label: 'Live CCTV Grid' },
    gis: { group: 'Live Surveillance', label: 'GIS Tactical Map' },
    cameras: { group: 'Live Surveillance', label: 'Camera Catalog' },
    search: { group: 'Vehicle Intelligence', label: 'Plate Search & Index' },
    correlation: { group: 'Vehicle Intelligence', label: 'Cross-Camera Re-ID' },
    watchlists: { group: 'Security & Hotlists', label: 'Hotlists & Watchlists' },
    alerts: { group: 'Security & Hotlists', label: 'Real-Time Alert Triage' },
    evidence: { group: 'Forensics & Integrity', label: 'Evidence Vault (SHA-256)' },
    audit: { group: 'Forensics & Integrity', label: 'Immutable Audit Trail' },
    system: { group: 'Diagnostics', label: 'System Health & Telemetry' },
  };

  const current = tabTitles[activeTab] || { group: 'System', label: activeTab };

  return (
    <nav className="flex items-center gap-2 text-xs font-mono text-slate-400 py-1 select-none">
      <button
        onClick={() => onTabChange('dashboard')}
        className="flex items-center gap-1 hover:text-white transition-colors"
      >
        <Home className="h-3.5 w-3.5 text-blue-400" />
        <span>Command</span>
      </button>

      <ChevronRight className="h-3 w-3 text-slate-600" />
      <span className="text-slate-400">{current.group}</span>

      <ChevronRight className="h-3 w-3 text-slate-600" />
      <span className="text-slate-100 font-semibold">{current.label}</span>

      {subTitle && (
        <>
          <ChevronRight className="h-3 w-3 text-slate-600" />
          <span className="text-blue-400 font-bold bg-blue-950/60 px-2 py-0.5 rounded border border-blue-800/60">
            {subTitle}
          </span>
        </>
      )}
    </nav>
  );
};
