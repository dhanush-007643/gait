import React from 'react';
import { Loader2 } from 'lucide-react';

interface LoadingStateProps { message?: string; rows?: number; }

function SkeletonRow() {
  return (
    <div className="flex gap-4 p-4 border-b border-slate-100 animate-pulse">
      <div className="w-24 h-4 bg-slate-200 rounded skeleton" />
      <div className="w-16 h-4 bg-slate-200 rounded skeleton" />
      <div className="w-20 h-4 bg-slate-200 rounded skeleton" />
      <div className="flex-1 h-4 bg-slate-200 rounded skeleton" />
    </div>
  );
}

export function TableLoadingState({ rows = 5 }: { rows?: number }) {
  return (
    <div>
      {Array.from({ length: rows }).map((_, i) => <SkeletonRow key={i} />)}
    </div>
  );
}

export function CardLoadingState() {
  return (
    <div className="card p-5 animate-pulse space-y-3">
      <div className="w-1/3 h-4 bg-slate-200 rounded skeleton" />
      <div className="w-1/2 h-8 bg-slate-200 rounded skeleton" />
      <div className="w-2/3 h-3 bg-slate-200 rounded skeleton" />
    </div>
  );
}

export default function LoadingState({ message = 'Loading...' }: LoadingStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-20 gap-3">
      <Loader2 className="w-8 h-8 text-primary-500 animate-spin" />
      <p className="text-sm text-slate-500">{message}</p>
    </div>
  );
}
