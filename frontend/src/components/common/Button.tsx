import React from 'react';
import { Loader2 } from 'lucide-react';

export type ButtonVariant = 'primary' | 'secondary' | 'danger' | 'warning' | 'ghost' | 'outline';
export type ButtonSize = 'sm' | 'md' | 'lg';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
  icon?: React.ReactNode;
  children?: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'md',
  loading = false,
  icon,
  children,
  className = '',
  disabled,
  ...props
}) => {
  const sizeStyles = {
    sm: 'px-2.5 py-1 text-xs gap-1.5',
    md: 'px-3.5 py-2 text-sm gap-2',
    lg: 'px-5 py-2.5 text-base gap-2.5',
  };

  const variantStyles = {
    primary:
      'bg-blue-600 hover:bg-blue-500 text-white font-medium shadow-[0_0_12px_rgba(37,99,235,0.35)] border border-blue-500/50 active:bg-blue-700',
    secondary:
      'bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium border border-slate-700 active:bg-slate-900',
    danger:
      'bg-rose-600 hover:bg-rose-500 text-white font-medium shadow-[0_0_12px_rgba(225,29,72,0.4)] border border-rose-500/50 active:bg-rose-700',
    warning:
      'bg-amber-600 hover:bg-amber-500 text-white font-medium shadow-[0_0_12px_rgba(217,119,6,0.35)] border border-amber-500/50 active:bg-amber-700',
    ghost:
      'bg-transparent hover:bg-slate-800/80 text-slate-300 hover:text-white border border-transparent',
    outline:
      'bg-transparent hover:bg-blue-950/40 text-blue-400 hover:text-blue-300 border border-blue-600/60 shadow-[0_0_8px_rgba(59,130,246,0.15)]',
  };

  return (
    <button
      className={`inline-flex items-center justify-center rounded-lg transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-blue-500/40 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer select-none ${sizeStyles[size]} ${variantStyles[variant]} ${className}`}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? (
        <Loader2 className="h-4 w-4 animate-spin text-current" />
      ) : (
        icon && <span className="flex-shrink-0">{icon}</span>
      )}
      {children && <span>{children}</span>}
    </button>
  );
};
