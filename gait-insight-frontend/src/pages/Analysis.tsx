import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Download, CheckCircle, AlertCircle, Info } from 'lucide-react';
import {
  BarChart, Bar, Cell, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Legend,
} from 'recharts';
import Layout from '../components/layout/Layout';
import ChartCard from '../components/ui/ChartCard';
import GaitBadge from '../components/ui/GaitBadge';
import SensorChart from '../components/ui/SensorChart';
import LoadingState from '../components/ui/LoadingState';
import ErrorState from '../components/ui/ErrorState';
import { sessionsApi } from '../services/api';
import type { SessionDetail as SD, GaitClass } from '../types';
import { generateSensorPoints, GAIT_COLORS_MAP } from '../data/mockData';

const PARAM_ROWS = [
  { key: 'cadence',       label: 'Cadence',       unit: 'steps/min', ref: '100–120' },
  { key: 'walking_speed', label: 'Walking Speed',  unit: 'm/s',       ref: '1.2–1.5' },
  { key: 'step_length',   label: 'Step Length',    unit: 'm',         ref: '0.65–0.75' },
  { key: 'stride_length', label: 'Stride Length',  unit: 'm',         ref: '1.3–1.5' },
  { key: 'step_time',     label: 'Step Time',      unit: 's',         ref: '0.5–0.6' },
  { key: 'stride_time',   label: 'Stride Time',    unit: 's',         ref: '1.0–1.2' },
  { key: 'stance_time',   label: 'Stance Time',    unit: 's',         ref: '0.6–0.7' },
  { key: 'swing_time',    label: 'Swing Time',     unit: 's',         ref: '0.35–0.45' },
  { key: 'gait_symmetry', label: 'Gait Symmetry',  unit: 'ratio',     ref: '0.95–1.0' },
];

export default function Analysis() {
  const { id } = useParams<{ id?: string }>();
  const navigate = useNavigate();

  const [detail, setDetail] = useState<SD | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState('');

  const load = async () => {
    setLoading(true);
    setError('');
    try {
      let targetId = id;
      if (!targetId) {
        const all = await sessionsApi.getAll({ per_page: 1 });
        if (all.items && all.items.length > 0) {
          targetId = all.items[0].session_id;
        } else {
          setError('No recorded gait sessions found. Please upload a CSV file to perform analysis.');
          setLoading(false);
          return;
        }
      }
      const data = await sessionsApi.getById(targetId);
      setDetail(data);
    } catch (e: any) {
      setError(e?.response?.data?.error ?? e?.message ?? 'Unable to load analysis.');
    } finally {
      setLoading(false);
    }
  };
  useEffect(() => { load(); }, [id]);

  if (loading) return <Layout title="Analysis"><LoadingState message="Loading analysis results..." /></Layout>;
  if (error || !detail) return <Layout title="Analysis"><ErrorState message={error} onRetry={load} /></Layout>;

  const { session, features, prediction } = detail;
  const predClass = (prediction?.predicted_class ?? 'normal') as GaitClass;
  const color = GAIT_COLORS_MAP[predClass] || '#22c55e';
  const isNormal = predClass === 'normal';
  const sensorData = generateSensorPoints(200, predClass);


  const probData = Object.entries(prediction?.probabilities ?? { normal: 1.0 }).map(([name, value]) => ({
    name: name.charAt(0).toUpperCase() + name.slice(1),
    value: parseFloat(((value || 0) * 100).toFixed(1)),
    fill: GAIT_COLORS_MAP[name as GaitClass] || '#64748b',
  }));

  const radarData = [
    { axis: 'Cadence',   value: Math.min((features?.cadence || 108) / 1.4, 100) },
    { axis: 'Speed',     value: Math.min((features?.walking_speed || 1.25) / 0.016, 100) },
    { axis: 'Symmetry',  value: (features?.gait_symmetry || 0.92) * 100 },
    { axis: 'Step Len',  value: Math.min((features?.step_length || 0.68) / 0.0085, 100) },
    { axis: 'Stride',    value: Math.min((features?.stride_length || 1.36) / 0.016, 100) },
    { axis: 'Balance',   value: Math.max(0, 100 - (features?.acceleration_std || 1.8) * 10) },
  ];


  const formatDate = (d?: string) => {
    if (!d) return '—';
    try {
      const parsed = new Date(d.includes(' ') && !d.includes('T') ? d.replace(' ', 'T') : d);
      return isNaN(parsed.getTime()) ? d : parsed.toLocaleString();
    } catch {
      return d;
    }
  };

  return (
    <Layout title="Analysis Results">
      {/* Header bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 mb-5">
        <div>
          <p className="text-xs text-slate-500">Session: <span className="font-mono font-semibold text-slate-700">{session.session_id}</span> · Subject: <span className="font-semibold text-slate-700">{session.subject_id}</span></p>
          <p className="text-xs text-slate-400 mt-0.5">{formatDate(session.session_date)}</p>
        </div>
        <div className="flex gap-2">
          <button onClick={() => navigate('/sessions')} className="btn-secondary text-xs py-1.5 px-3">
            <ArrowLeft className="w-3.5 h-3.5" /> Back to Sessions
          </button>
          <button className="btn-primary text-xs py-1.5 px-3" onClick={() => navigate(`/reports/${session.session_id}`)}>
            <Download className="w-3.5 h-3.5" /> Download Report
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 mb-5">
        {/* Prediction card */}
        <div className="card p-6 flex flex-col items-center text-center">
          <div className="w-16 h-16 rounded-full flex items-center justify-center mb-4"
            style={{ backgroundColor: `${color}18` }}>
            {isNormal
              ? <CheckCircle className="w-8 h-8" style={{ color }} />
              : <AlertCircle className="w-8 h-8" style={{ color }} />}
          </div>
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">Predicted Gait Pattern</p>
          <p className="text-2xl font-extrabold uppercase mb-2" style={{ color }}>
            {predClass}
          </p>
          <GaitBadge gaitClass={predClass} size="md" />
          <div className="mt-5 w-full">
            <p className="text-xs text-slate-500 mb-1">Confidence Score</p>
            <p className="text-4xl font-black" style={{ color }}>
              {((prediction?.confidence_score ?? 0) * 100).toFixed(1)}%
            </p>
            <div className="mt-2 w-full bg-slate-100 rounded-full h-2">
              <div className="h-2 rounded-full transition-all" style={{ width: `${(prediction?.confidence_score ?? 0) * 100}%`, backgroundColor: color }} />
            </div>
          </div>
          <div className="mt-4 text-left w-full pt-4 border-t border-slate-100 space-y-1.5">
            <p className="text-xs text-slate-500">Model: <span className="text-slate-700 font-medium">{prediction?.model_name || 'Random Forest'}</span></p>
            <p className="text-xs text-slate-500">Version: <span className="text-slate-700 font-medium">{prediction?.model_version || '1.0.0'}</span></p>
          </div>
        </div>

        {/* Parameters table */}
        <div className="lg:col-span-2 card p-5">
          <h3 className="font-semibold text-slate-800 mb-4">Gait Parameters</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-100">
                  <th className="text-left py-2 text-xs font-semibold text-slate-500">Parameter</th>
                  <th className="text-right py-2 text-xs font-semibold text-slate-500">Value</th>
                  <th className="text-right py-2 text-xs font-semibold text-slate-500">Unit</th>
                  <th className="text-right py-2 text-xs font-semibold text-slate-500">Normal Range</th>
                </tr>
              </thead>
              <tbody>
                {PARAM_ROWS.map(({ key, label, unit, ref }) => (
                  <tr key={key} className="border-b border-slate-50 hover:bg-slate-50">
                    <td className="py-2.5 font-medium text-slate-700">{label}</td>
                    <td className="py-2.5 text-right font-semibold text-slate-800">
                      {(features as any)[key]?.toFixed(3) ?? '—'}
                    </td>
                    <td className="py-2.5 text-right text-slate-400 text-xs">{unit}</td>
                    <td className="py-2.5 text-right text-slate-400 text-xs">{ref}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 mb-5">
        <ChartCard title="Class Probability Distribution" subtitle="Prediction confidence per gait class (%)">
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={probData} layout="vertical" margin={{ left: 20, right: 10 }}>
              <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#f1f5f9" />
              <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 10, fill: '#94a3b8' }} tickLine={false} axisLine={false} unit="%" />
              <YAxis type="category" dataKey="name" tick={{ fontSize: 11, fill: '#64748b' }} tickLine={false} axisLine={false} width={90} />
              <Tooltip formatter={(v: any) => [`${v}%`]} contentStyle={{ borderRadius: '8px', fontSize: '12px' }} />
              <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                {probData.map((entry, i) => (
                  <Cell key={i} fill={entry.fill} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Gait Parameter Radar" subtitle="Normalised biomechanical parameters">
          <ResponsiveContainer width="100%" height={200}>
            <RadarChart data={radarData}>
              <PolarGrid stroke="#e2e8f0" />
              <PolarAngleAxis dataKey="axis" tick={{ fontSize: 10, fill: '#64748b' }} />
              <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fontSize: 8, fill: '#94a3b8' }} />
              <Radar name="Subject" dataKey="value" stroke={color} fill={color} fillOpacity={0.25} strokeWidth={2} />
              <Legend wrapperStyle={{ fontSize: '11px' }} />
            </RadarChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Illustrative Acceleration" subtitle="Synthetic example; not the uploaded recording">
          <SensorChart data={sensorData} type="acceleration" height={180} />
        </ChartCard>

        <ChartCard title="Illustrative Gyroscope" subtitle="Synthetic example; not the uploaded recording">
          <SensorChart data={sensorData} type="gyroscope" height={180} />
        </ChartCard>
      </div>

      {/* Disclaimer */}
      <div className="flex items-start gap-2.5 p-4 bg-blue-50 border border-blue-200 rounded-xl">
        <Info className="w-4 h-4 text-blue-500 flex-shrink-0 mt-0.5" />
        <p className="text-xs text-blue-700 leading-relaxed">
          This application is a research/educational prototype for gait pattern analysis and is not a medical diagnostic device.
          Results should not replace assessment by a qualified healthcare professional.
        </p>
      </div>
    </Layout>
  );
}
