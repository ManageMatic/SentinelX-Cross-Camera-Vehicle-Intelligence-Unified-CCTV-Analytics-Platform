import React from 'react';
import { ArrowUpRight, ArrowDownRight } from 'lucide-react';

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ReactNode;
  trend?: {
    value: string;
    isPositive?: boolean;
    label?: string;
  };
  badge?: React.ReactNode;
  color?: 'blue' | 'red' | 'green' | 'amber' | 'purple' | 'cyan';
  className?: string;
  onClick?: () => void;
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  subtitle,
  icon,
  trend,
  badge,
  color = 'blue',
  className = '',
  onClick,
}) => {
  const colorMap = {
    blue: {
      border: 'border-blue-900/60 hover:border-blue-600/70',
      glow: 'shadow-[0_0_15px_rgba(59,130,246,0.1)]',
      iconBg: 'bg-blue-950/80 text-blue-400 border border-blue-800/60',
      accent: 'text-blue-400',
    },
    red: {
      border: 'border-rose-900/60 hover:border-rose-600/70',
      glow: 'shadow-[0_0_15px_rgba(244,63,94,0.15)]',
      iconBg: 'bg-rose-950/80 text-rose-400 border border-rose-800/60',
      accent: 'text-rose-400',
    },
    green: {
      border: 'border-emerald-900/60 hover:border-emerald-600/70',
      glow: 'shadow-[0_0_15px_rgba(16,185,129,0.1)]',
      iconBg: 'bg-emerald-950/80 text-emerald-400 border border-emerald-800/60',
      accent: 'text-emerald-400',
    },
    amber: {
      border: 'border-amber-900/60 hover:border-amber-600/70',
      glow: 'shadow-[0_0_15px_rgba(245,158,11,0.1)]',
      iconBg: 'bg-amber-950/80 text-amber-400 border border-amber-800/60',
      accent: 'text-amber-400',
    },
    purple: {
      border: 'border-purple-900/60 hover:border-purple-600/70',
      glow: 'shadow-[0_0_15px_rgba(168,85,247,0.1)]',
      iconBg: 'bg-purple-950/80 text-purple-400 border border-purple-800/60',
      accent: 'text-purple-400',
    },
    cyan: {
      border: 'border-cyan-900/60 hover:border-cyan-600/70',
      glow: 'shadow-[0_0_15px_rgba(6,182,212,0.1)]',
      iconBg: 'bg-cyan-950/80 text-cyan-400 border border-cyan-800/60',
      accent: 'text-cyan-400',
    },
  };

  const style = colorMap[color];

  return (
    <div
      onClick={onClick}
      className={`relative bg-[#0d1424]/90 rounded-xl p-5 border transition-all duration-200 backdrop-blur-md ${
        onClick ? 'cursor-pointer hover:scale-[1.01]' : ''
      } ${style.border} ${style.glow} ${className}`}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <p className="text-xs font-mono font-semibold uppercase tracking-wider text-slate-400 truncate">
            {title}
          </p>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl lg:text-3xl font-bold font-mono tracking-tight text-white">
              {value}
            </span>
            {badge && <span>{badge}</span>}
          </div>
          {subtitle && <p className="text-xs text-slate-400 mt-1">{subtitle}</p>}
        </div>
        <div className={`p-3 rounded-lg flex-shrink-0 ${style.iconBg}`}>{icon}</div>
      </div>

      {trend && (
        <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs">
          <div
            className={`flex items-center gap-1 font-semibold ${
              trend.isPositive ? 'text-emerald-400' : 'text-rose-400'
            }`}
          >
            {trend.isPositive ? (
              <ArrowUpRight className="h-3.5 w-3.5" />
            ) : (
              <ArrowDownRight className="h-3.5 w-3.5" />
            )}
            <span>{trend.value}</span>
          </div>
          {trend.label && <span className="text-slate-400">{trend.label}</span>}
        </div>
      )}
    </div>
  );
};
