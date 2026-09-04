import React from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import clsx from 'clsx';

interface PaginationProps {
  page: number;
  totalPages: number;
  onPageChange: (p: number) => void;
}

export default function Pagination({ page, totalPages, onPageChange }: PaginationProps) {
  if (totalPages <= 1) return null;
  const pages = Array.from({ length: Math.min(totalPages, 5) }, (_, i) => {
    if (totalPages <= 5) return i + 1;
    if (page <= 3) return i + 1;
    if (page >= totalPages - 2) return totalPages - 4 + i;
    return page - 2 + i;
  });

  return (
    <div className="flex items-center gap-1" role="navigation" aria-label="Pagination">
      <button onClick={() => onPageChange(page - 1)} disabled={page === 1}
        className="w-8 h-8 flex items-center justify-center rounded-lg border border-slate-200 text-slate-500 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed" aria-label="Previous page">
        <ChevronLeft className="w-4 h-4" />
      </button>
      {pages.map(p => (
        <button key={p} onClick={() => onPageChange(p)}
          className={clsx('w-8 h-8 flex items-center justify-center rounded-lg text-sm font-medium border transition-colors',
            p === page ? 'bg-primary-600 text-white border-primary-600' : 'border-slate-200 text-slate-600 hover:bg-slate-50')}
          aria-current={p === page ? 'page' : undefined}>
          {p}
        </button>
      ))}
      <button onClick={() => onPageChange(page + 1)} disabled={page === totalPages}
        className="w-8 h-8 flex items-center justify-center rounded-lg border border-slate-200 text-slate-500 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed" aria-label="Next page">
        <ChevronRight className="w-4 h-4" />
      </button>
    </div>
  );
}
