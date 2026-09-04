import React from 'react';
import clsx from 'clsx';

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ReactNode;
  iconBg?: string;
  trend?: string;
  trendUp?: boolean;
}

export default function StatCard({ title, value, subtitle, icon, iconBg = 'bg-primary-50', trend, trendUp }: StatCardProps) {
  return (
    <div className="card p-5 hover:shadow-card-md transition-shadow">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-slate-500 truncate">{title}</p>
          <p className="text-2xl font-bold text-slate-900 mt-1.5">{value}</p>
          {subtitle && <p className="text-sm text-slate-500 mt-1">{subtitle}</p>}
          {trend && (
            <p className={clsx('text-xs font-medium mt-2', trendUp ? 'text-green-600' : 'text-slate-500')}>
              {trend}
            </p>
          )}
        </div>
        <div className={clsx('w-11 h-11 rounded-xl flex items-center justify-center flex-shrink-0', iconBg)}>
          {icon}
        </div>
      </div>
    </div>
  );
}
