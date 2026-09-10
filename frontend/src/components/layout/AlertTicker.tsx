import React from 'react';
import { AlertTriangle, ChevronRight } from 'lucide-react';
import { AlertItem } from '../../types';

interface AlertTickerProps {
  alerts: AlertItem[];
  onSelectAlert: (alert: AlertItem) => void;
}

export const AlertTicker: React.FC<AlertTickerProps> = ({ alerts, onSelectAlert }) => {
  if (!alerts || alerts.length === 0) return null;

  return (
    <div className="bg-gradient-to-r from-rose-950 via-rose-900 to-rose-950 border-y border-rose-600/60 px-4 py-1.5 flex items-center gap-3 overflow-hidden select-none shadow-[0_0_15px_rgba(225,29,72,0.25)]">
      {/* Ticker Title Badge */}
      <div className="flex items-center gap-1.5 px-2.5 py-0.5 rounded bg-rose-600 text-white font-mono font-black text-[11px] tracking-wider uppercase flex-shrink-0 shadow-sm animate-pulse">
        <AlertTriangle className="h-3.5 w-3.5" />
        <span>HOTLIST HIT</span>
      </div>

      {/* Marquee Content */}
      <div className="flex-1 overflow-hidden relative">
        <div className="animate-marquee whitespace-nowrap flex items-center gap-8 text-xs font-mono">
          {alerts.concat(alerts).map((alert, index) => (
            <div
              key={`${alert.id}-${index}`}
              onClick={() => onSelectAlert(alert)}
              className="inline-flex items-center gap-2 cursor-pointer text-rose-100 hover:text-white hover:underline transition-all"
            >
              <span className="font-bold bg-black/40 px-2 py-0.5 rounded border border-rose-500/50 text-yellow-300">
                {alert.plate_number}
              </span>
              <span className="text-rose-200">
                [{alert.category}] {alert.watchlist_name} detected at{' '}
                <strong className="text-white">{alert.camera_name}</strong> ({alert.location})
              </span>
              <span className="text-[10px] text-rose-300">
                {new Date(alert.timestamp).toLocaleTimeString()}
              </span>
              <ChevronRight className="h-3 w-3 text-rose-400" />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
