import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

interface ErrorStateProps { message?: string; onRetry?: () => void; }

export default function ErrorState({ message = 'Unable to load gait data. Please try again.', onRetry }: ErrorStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-20 gap-4 text-center">
      <div className="w-16 h-16 rounded-full bg-red-50 flex items-center justify-center">
        <AlertTriangle className="w-7 h-7 text-red-400" />
      </div>
      <div>
        <p className="font-semibold text-slate-700">Something went wrong</p>
        <p className="text-sm text-slate-500 mt-1 max-w-sm">{message}</p>
      </div>
      {onRetry && (
        <button onClick={onRetry} className="btn-secondary">
          <RefreshCw className="w-4 h-4" /> Try Again
        </button>
      )}
    </div>
  );
}
