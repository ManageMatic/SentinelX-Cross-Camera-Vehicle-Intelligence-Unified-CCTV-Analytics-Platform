import React from 'react';
import { TopNav } from './TopNav';
import { Sidebar } from './Sidebar';
import { AlertTicker } from './AlertTicker';
import { Breadcrumbs } from './Breadcrumbs';
import { NavigationTab, SystemHealthResponse, AlertItem } from '../../types';

interface AppLayoutProps {
  activeTab: NavigationTab;
  onTabChange: (tab: NavigationTab) => void;
  health: SystemHealthResponse | null;
  loading: boolean;
  activeAlerts: AlertItem[];
  onSelectAlert: (alert: AlertItem) => void;
  onQuickSearch: (query: string) => void;
  isAudioAlertEnabled: boolean;
  onToggleAudioAlert: () => void;
  subTitle?: string;
  children: React.ReactNode;
}

export const AppLayout: React.FC<AppLayoutProps> = ({
  activeTab,
  onTabChange,
  health,
  loading,
  activeAlerts,
  onSelectAlert,
  onQuickSearch,
  isAudioAlertEnabled,
  onToggleAudioAlert,
  subTitle,
  children,
}) => {
  return (
    <div className="min-h-screen flex flex-col bg-[#070a12] text-slate-100 antialiased font-sans">
      {/* Top Tactical Navigation */}
      <TopNav
        health={health}
        loading={loading}
        activeAlerts={activeAlerts}
        onOpenAlerts={() => onTabChange('alerts')}
        onQuickSearch={onQuickSearch}
        isAudioAlertEnabled={isAudioAlertEnabled}
        onToggleAudioAlert={onToggleAudioAlert}
      />

      {/* Real-time Emergency Hit Ticker */}
      <AlertTicker alerts={activeAlerts} onSelectAlert={onSelectAlert} />

      {/* Main Workspace Frame */}
      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar Navigation */}
        <Sidebar
          activeTab={activeTab}
          onTabChange={onTabChange}
          activeAlertCount={activeAlerts.length}
        />

        {/* Content View Area */}
        <main className="flex-1 overflow-y-auto bg-[#070a12] bg-tactical-grid flex flex-col">
          <div className="px-4 sm:px-6 lg:px-8 py-3 border-b border-slate-800/80 bg-[#080d19]/80 backdrop-blur-sm sticky top-0 z-20">
            <Breadcrumbs activeTab={activeTab} onTabChange={onTabChange} subTitle={subTitle} />
          </div>
          <div className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto w-full">{children}</div>
        </main>
      </div>
    </div>
  );
};
