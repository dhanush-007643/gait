import React from 'react';
import { Inbox } from 'lucide-react';

interface EmptyStateProps { title?: string; message?: string; action?: React.ReactNode; }

export default function EmptyState({ title = 'No data found', message = 'No gait sessions found. Upload a CSV to get started.', action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-20 gap-4 text-center">
      <div className="w-16 h-16 rounded-full bg-slate-100 flex items-center justify-center">
        <Inbox className="w-7 h-7 text-slate-400" />
      </div>
      <div>
        <p className="font-semibold text-slate-700">{title}</p>
        <p className="text-sm text-slate-500 mt-1 max-w-sm">{message}</p>
      </div>
      {action}
    </div>
  );
}
