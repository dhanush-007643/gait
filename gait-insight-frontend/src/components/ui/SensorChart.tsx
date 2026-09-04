import React from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts';
import type { SensorPoint } from '../../types';

interface SensorChartProps {
  data: SensorPoint[];
  type?: 'acceleration' | 'gyroscope';
  height?: number;
  maxPoints?: number;
}

const ACC_LINES = [
  { key: 'acceleration_x', color: '#6366f1', label: 'X-axis' },
  { key: 'acceleration_y', color: '#22c55e', label: 'Y-axis' },
  { key: 'acceleration_z', color: '#f97316', label: 'Z-axis' },
];
const GYRO_LINES = [
  { key: 'gyroscope_x', color: '#6366f1', label: 'X-axis' },
  { key: 'gyroscope_y', color: '#22c55e', label: 'Y-axis' },
  { key: 'gyroscope_z', color: '#f97316', label: 'Z-axis' },
];

export default function SensorChart({ data, type = 'acceleration', height = 220, maxPoints = 100 }: SensorChartProps) {
  const lines = type === 'acceleration' ? ACC_LINES : GYRO_LINES;
  const unit  = type === 'acceleration' ? 'm/s²' : '°/s';
  const displayData = data.slice(-maxPoints);

  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={displayData} margin={{ top: 4, right: 8, left: -10, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
        <XAxis
          dataKey="timestamp"
          tickFormatter={(v: number) => `${v.toFixed(1)}s`}
          tick={{ fontSize: 10, fill: '#94a3b8' }}
          tickLine={false}
          axisLine={false}
        />
        <YAxis
          tick={{ fontSize: 10, fill: '#94a3b8' }}
          tickLine={false}
          axisLine={false}
          unit={` ${unit}`}
        />
        <Tooltip
          contentStyle={{ borderRadius: '8px', border: '1px solid #e2e8f0', fontSize: '12px' }}
          labelFormatter={(v: number) => `t = ${v.toFixed(2)}s`}
          formatter={(v: number, name: string) => [`${v.toFixed(3)} ${unit}`, name]}
        />
        <Legend wrapperStyle={{ fontSize: '11px' }} />
        {lines.map(({ key, color, label }) => (
          <Line
            key={key}
            type="monotone"
            dataKey={key}
            stroke={color}
            strokeWidth={1.5}
            dot={false}
            name={label}
            isAnimationActive={false}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}
