import React from 'react';
import { AlertPriority, AlertStatus, WatchlistCategory, CameraStatus } from '../../types';

export type BadgeVariant =
  | 'default'
  | 'primary'
  | 'success'
  | 'danger'
  | 'warning'
  | 'info'
  | 'purple'
  | 'cyan';

interface BadgeProps {
  children: React.ReactNode;
  variant?: BadgeVariant;
  size?: 'sm' | 'md' | 'lg';
  dot?: boolean;
  pulse?: boolean;
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'default',
  size = 'md',
  dot = false,
  pulse = false,
  className = '',
}) => {
  const sizeStyles = {
    sm: 'px-2 py-0.5 text-[10px] font-semibold tracking-wide',
    md: 'px-2.5 py-1 text-xs font-semibold tracking-wide',
    lg: 'px-3 py-1.5 text-sm font-semibold tracking-wide',
  };

  const variantStyles: Record<BadgeVariant, { container: string; dot: string }> = {
    default: {
      container: 'bg-slate-800/80 text-slate-300 border border-slate-700',
      dot: 'bg-slate-400',
    },
    primary: {
      container: 'bg-blue-950/80 text-blue-300 border border-blue-700/60 shadow-[0_0_8px_rgba(59,130,246,0.2)]',
      dot: 'bg-blue-400',
    },
    success: {
      container: 'bg-emerald-950/80 text-emerald-300 border border-emerald-700/60 shadow-[0_0_8px_rgba(16,185,129,0.2)]',
      dot: 'bg-emerald-400',
    },
    danger: {
      container: 'bg-rose-950/80 text-rose-300 border border-rose-700/60 shadow-[0_0_8px_rgba(244,63,94,0.3)]',
      dot: 'bg-rose-400',
    },
    warning: {
      container: 'bg-amber-950/80 text-amber-300 border border-amber-700/60 shadow-[0_0_8px_rgba(245,158,11,0.2)]',
      dot: 'bg-amber-400',
    },
    info: {
      container: 'bg-sky-950/80 text-sky-300 border border-sky-700/60 shadow-[0_0_8px_rgba(14,165,233,0.2)]',
      dot: 'bg-sky-400',
    },
    purple: {
      container: 'bg-purple-950/80 text-purple-300 border border-purple-700/60 shadow-[0_0_8px_rgba(168,85,247,0.2)]',
      dot: 'bg-purple-400',
    },
    cyan: {
      container: 'bg-cyan-950/80 text-cyan-300 border border-cyan-700/60 shadow-[0_0_8px_rgba(6,182,212,0.2)]',
      dot: 'bg-cyan-400',
    },
  };

  const style = variantStyles[variant] || variantStyles.default;

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-md uppercase font-mono tracking-wider transition-all duration-200 ${sizeStyles[size]} ${style.container} ${className}`}
    >
      {dot && (
        <span
          className={`h-1.5 w-1.5 rounded-full ${style.dot} ${
            pulse ? 'animate-pulse' : ''
          }`}
        />
      )}
      {children}
    </span>
  );
};

export const PriorityBadge: React.FC<{ priority: AlertPriority }> = ({ priority }) => {
  const map: Record<AlertPriority, { variant: BadgeVariant; label: string }> = {
    CRITICAL: { variant: 'danger', label: 'CRITICAL' },
    HIGH: { variant: 'danger', label: 'HIGH' },
    MEDIUM: { variant: 'warning', label: 'MEDIUM' },
    LOW: { variant: 'info', label: 'LOW' },
  };
  const config = map[priority] || { variant: 'default', label: priority };
  return (
    <Badge variant={config.variant} dot={priority === 'CRITICAL'} pulse={priority === 'CRITICAL'}>
      {config.label}
    </Badge>
  );
};

export const StatusBadge: React.FC<{ status: AlertStatus }> = ({ status }) => {
  const map: Record<AlertStatus, { variant: BadgeVariant; label: string }> = {
    NEW: { variant: 'danger', label: 'NEW' },
    ACKNOWLEDGED: { variant: 'warning', label: 'ACKNOWLEDGED' },
    RESOLVED: { variant: 'success', label: 'RESOLVED' },
    FALSE_POSITIVE: { variant: 'default', label: 'FALSE POSITIVE' },
  };
  const config = map[status] || { variant: 'default', label: status };
  return (
    <Badge variant={config.variant} dot>
      {config.label}
    </Badge>
  );
};

export const CategoryBadge: React.FC<{ category: WatchlistCategory }> = ({ category }) => {
  const map: Record<WatchlistCategory, { variant: BadgeVariant; label: string }> = {
    WANTED: { variant: 'danger', label: 'WANTED' },
    STOLEN: { variant: 'danger', label: 'STOLEN VEHICLE' },
    SUSPICIOUS: { variant: 'warning', label: 'SUSPICIOUS' },
    VIP: { variant: 'purple', label: 'VIP CONVOY' },
    SPECIAL_INTEREST: { variant: 'cyan', label: 'SPECIAL INTEREST' },
  };
  const config = map[category] || { variant: 'default', label: category };
  return <Badge variant={config.variant}>{config.label}</Badge>;
};

export const CameraStatusBadge: React.FC<{ status: CameraStatus; fps?: number }> = ({
  status,
  fps,
}) => {
  const map: Record<CameraStatus, { variant: BadgeVariant; label: string }> = {
    ONLINE: { variant: 'success', label: `ONLINE ${fps ? `(${fps} FPS)` : ''}` },
    OFFLINE: { variant: 'default', label: 'OFFLINE' },
    DEGRADED: { variant: 'warning', label: 'DEGRADED' },
    CONNECTING: { variant: 'info', label: 'CONNECTING' },
  };
  const config = map[status] || { variant: 'default', label: status };
  return (
    <Badge variant={config.variant} dot pulse={status === 'ONLINE'}>
      {config.label}
    </Badge>
  );
};
