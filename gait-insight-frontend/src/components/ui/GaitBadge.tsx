import React from 'react';
import type { GaitClass } from '../../types';
import { GAIT_COLORS_MAP } from '../../data/mockData';
import clsx from 'clsx';

const LABELS: Record<GaitClass, string> = {
  normal: 'Normal', parkinsonian: 'Parkinsonian',
  hemiplegic: 'Hemiplegic', ataxic: 'Ataxic',
  spastic: 'Spastic', antalgic: 'Antalgic',
};

interface GaitBadgeProps {
  gaitClass: GaitClass;
  size?: 'sm' | 'md' | 'lg';
  showDot?: boolean;
}

export default function GaitBadge({ gaitClass, size = 'md', showDot = true }: GaitBadgeProps) {
  const color = GAIT_COLORS_MAP[gaitClass];
  const label = LABELS[gaitClass];

  const sizeClass = {
    sm: 'text-xs px-2 py-0.5',
    md: 'text-xs px-2.5 py-1',
    lg: 'text-sm px-3 py-1.5',
  }[size];

  return (
    <span
      className={clsx('inline-flex items-center gap-1.5 rounded-full font-semibold', sizeClass)}
      style={{ backgroundColor: `${color}18`, color }}
      role="status"
      aria-label={`Gait classification: ${label}`}
    >
      {showDot && (
        <span className="w-1.5 h-1.5 rounded-full flex-shrink-0" style={{ backgroundColor: color }} aria-hidden="true" />
      )}
      {label}
    </span>
  );
}
