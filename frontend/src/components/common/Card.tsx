import React from 'react';

interface CardProps {
  children: React.ReactNode;
  title?: React.ReactNode;
  subtitle?: React.ReactNode;
  action?: React.ReactNode;
  icon?: React.ReactNode;
  variant?: 'default' | 'glow-blue' | 'glow-red' | 'ghost';
  className?: string;
  headerClassName?: string;
  bodyClassName?: string;
}

export const Card: React.FC<CardProps> = ({
  children,
  title,
  subtitle,
  action,
  icon,
  variant = 'default',
  className = '',
  headerClassName = '',
  bodyClassName = '',
}) => {
  const variantStyles = {
    default: 'bg-[#0f172a]/90 border border-slate-800 shadow-xl backdrop-blur-md',
    'glow-blue':
      'bg-[#0d172e]/90 border border-blue-600/50 shadow-[0_0_20px_rgba(37,99,235,0.15)] backdrop-blur-md',
    'glow-red':
      'bg-[#1f0d14]/90 border border-rose-600/50 shadow-[0_0_20px_rgba(225,29,72,0.2)] backdrop-blur-md',
    ghost: 'bg-transparent border border-slate-800/80',
  };

  return (
    <div className={`rounded-xl overflow-hidden ${variantStyles[variant]} ${className}`}>
      {(title || action || icon) && (
        <div
          className={`px-5 py-4 border-b border-slate-800/80 flex items-center justify-between gap-3 ${headerClassName}`}
        >
          <div className="flex items-center gap-3 min-w-0">
            {icon && <div className="text-blue-400 flex-shrink-0">{icon}</div>}
            <div className="min-w-0">
              {typeof title === 'string' ? (
                <h3 className="text-sm font-semibold text-white tracking-wide uppercase font-mono truncate">
                  {title}
                </h3>
              ) : (
                title
              )}
              {subtitle && <p className="text-xs text-slate-400 mt-0.5 truncate">{subtitle}</p>}
            </div>
          </div>
          {action && <div className="flex-shrink-0">{action}</div>}
        </div>
      )}
      <div className={`p-5 ${bodyClassName}`}>{children}</div>
    </div>
  );
};
