import React from 'react';

interface StatusCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ElementType;
  variant?: 'default' | 'accent' | 'warning' | 'alert' | 'success';
}

export const StatusCard: React.FC<StatusCardProps> = ({
  title,
  value,
  subtitle,
  icon: Icon,
  variant = 'default',
}) => {
  const getVariantStyles = () => {
    switch (variant) {
      case 'accent':
        return 'border-sky-500/30 bg-sky-950/20 text-sky-400';
      case 'warning':
        return 'border-amber-500/30 bg-amber-950/20 text-amber-400';
      case 'alert':
        return 'border-rose-500/30 bg-rose-950/20 text-rose-400';
      case 'success':
        return 'border-emerald-500/30 bg-emerald-950/20 text-emerald-400';
      default:
        return 'border-sentinel-700 bg-sentinel-850 text-slate-300';
    }
  };

  return (
    <div className={`p-5 rounded-xl border ${getVariantStyles()} flex items-start justify-between shadow-sm transition-all hover:border-sentinel-600`}>
      <div>
        <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">{title}</p>
        <p className="text-2xl font-bold text-white mt-1.5 font-mono">{value}</p>
        {subtitle && <p className="text-xs text-slate-400 mt-1">{subtitle}</p>}
      </div>
      <div className="p-2.5 rounded-lg bg-sentinel-800/80 border border-sentinel-700/50">
        <Icon className="w-5 h-5" />
      </div>
    </div>
  );
};
