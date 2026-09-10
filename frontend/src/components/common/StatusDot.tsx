import React from 'react';

export type StatusColor = 'green' | 'red' | 'amber' | 'blue' | 'gray';

interface StatusDotProps {
  status?: StatusColor;
  ping?: boolean;
  size?: 'sm' | 'md' | 'lg';
  label?: string;
  className?: string;
}

export const StatusDot: React.FC<StatusDotProps> = ({
  status = 'green',
  ping = true,
  size = 'md',
  label,
  className = '',
}) => {
  const sizeMap = {
    sm: 'h-1.5 w-1.5',
    md: 'h-2.5 w-2.5',
    lg: 'h-3.5 w-3.5',
  };

  const colorMap = {
    green: {
      bg: 'bg-emerald-500',
      ping: 'bg-emerald-400',
      glow: 'shadow-[0_0_8px_rgba(16,185,129,0.8)]',
    },
    red: {
      bg: 'bg-rose-500',
      ping: 'bg-rose-400',
      glow: 'shadow-[0_0_8px_rgba(244,63,94,0.8)]',
    },
    amber: {
      bg: 'bg-amber-500',
      ping: 'bg-amber-400',
      glow: 'shadow-[0_0_8px_rgba(245,158,11,0.8)]',
    },
    blue: {
      bg: 'bg-sky-500',
      ping: 'bg-sky-400',
      glow: 'shadow-[0_0_8px_rgba(14,165,233,0.8)]',
    },
    gray: {
      bg: 'bg-slate-500',
      ping: 'bg-slate-400',
      glow: '',
    },
  };

  const activeColor = colorMap[status] || colorMap.gray;

  return (
    <div className={`inline-flex items-center gap-2 ${className}`}>
      <span className="relative flex items-center justify-center">
        {ping && status !== 'gray' && (
          <span
            className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${activeColor.ping}`}
          />
        )}
        <span
          className={`relative inline-flex rounded-full ${sizeMap[size]} ${activeColor.bg} ${activeColor.glow}`}
        />
      </span>
      {label && <span className="text-xs font-medium text-slate-300">{label}</span>}
    </div>
  );
};
