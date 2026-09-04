import React, { useEffect, useState } from 'react';
import { Info } from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell,
} from 'recharts';
import Layout from '../components/layout/Layout';
import LoadingState from '../components/ui/LoadingState';
import ErrorState from '../components/ui/ErrorState';
import { modelApi } from '../services/api';
import type { ModelPerformance } from '../types';
import { GAIT_COLORS_MAP } from '../data/mockData';
import type { GaitClass } from '../types';

function MetricCard({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="card p-5 text-center">
      <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">{label}</p>
      <p className="text-4xl font-black mt-2" style={{ color }}>{(value * 100).toFixed(1)}%</p>
      <div className="mt-3 bg-slate-100 rounded-full h-2">
        <div className="h-2 rounded-full" style={{ width: `${value * 100}%`, backgroundColor: color }} />
      </div>
    </div>
  );
}

export default function ModelPerformance() {
  const [perf, setPerf]     = useState<ModelPerformance | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError]   = useState('');

  const load = async () => {
    setLoading(true);
    try { setPerf(await modelApi.getPerformance()); }
    catch { setError('Unable to load model performance data.'); }
    finally { setLoading(false); }
  };
  useEffect(() => { load(); }, []);

  if (loading) return <Layout title="Model Performance"><LoadingState /></Layout>;
  if (error || !perf) return <Layout title="Model Performance"><ErrorState message={error} onRetry={load} /></Layout>;

  const f1Data = Object.entries(perf.per_class_f1).map(([cls, score]) => ({
    name: cls.charAt(0).toUpperCase() + cls.slice(1),
    f1: parseFloat((score * 100).toFixed(1)),
    color: GAIT_COLORS_MAP[cls as GaitClass],
  }));

  const confMatrix = perf.confusion_matrix;
  const labels = perf.class_names.map(c => c.charAt(0).toUpperCase() + c.slice(1));

  return (
    <Layout title="Model Performance" subtitle="Machine Learning evaluation metrics and diagnostics">
      {/* Metric cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <MetricCard label="Accuracy"  value={perf.accuracy}         color="#6366f1" />
        <MetricCard label="Precision" value={perf.precision_score}  color="#22c55e" />
        <MetricCard label="Recall"    value={perf.recall_score}     color="#f97316" />
        <MetricCard label="F1 Score"  value={perf.f1_score}         color="#a855f7" />
      </div>

      {/* Meta info */}
      <div className="card p-5 mb-5">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {[
            { l: 'Model Name',      v: perf.model_name },
            { l: 'Version',         v: perf.model_version },
            { l: 'Training Samples',v: perf.training_samples },
            { l: 'Testing Samples', v: perf.testing_samples },
            { l: 'Training Date',   v: new Date(perf.training_date).toLocaleDateString() },
            { l: 'Algorithm',       v: 'Random Forest' },
            { l: 'Gait Classes',    v: 6 },
            { l: 'Features',        v: '16 biomechanical' },
          ].map(({ l, v }) => (
            <div key={l}>
              <p className="text-xs text-slate-500">{l}</p>
              <p className="font-semibold text-slate-800 text-sm mt-0.5">{v}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 mb-5">
        {/* Class-wise F1 */}
        <div className="card p-5">
          <h3 className="font-semibold text-slate-800 mb-4">Class-wise F1 Score (%)</h3>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={f1Data} margin={{ left: -10 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
              <XAxis dataKey="name" tick={{ fontSize: 10, fill: '#64748b' }} tickLine={false} axisLine={false} />
              <YAxis domain={[0, 100]} tick={{ fontSize: 10, fill: '#94a3b8' }} tickLine={false} axisLine={false} unit="%" />
              <Tooltip formatter={(v: any) => [`${v}%`]} contentStyle={{ borderRadius: '8px', fontSize: '12px' }} />
              <Bar dataKey="f1" radius={[4, 4, 0, 0]}>
                {f1Data.map((entry, i) => <Cell key={i} fill={entry.color} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Confusion matrix */}
        <div className="card p-5">
          <h3 className="font-semibold text-slate-800 mb-4">Confusion Matrix</h3>
          <div className="overflow-auto">
            <table className="text-xs w-full text-center">
              <thead>
                <tr>
                  <th className="py-1 px-1 text-slate-400">Actual ↓ Pred →</th>
                  {labels.map(l => <th key={l} className="py-1 px-1 font-semibold text-slate-600 rotate-0">{l.slice(0,4)}</th>)}
                </tr>
              </thead>
              <tbody>
                {confMatrix.map((row, ri) => (
                  <tr key={ri}>
                    <td className="py-1 px-2 font-semibold text-slate-600 text-left">{labels[ri]}</td>
                    {row.map((val, ci) => {
                      const isCorrect = ri === ci;
                      const maxVal = Math.max(...row);
                      const opacity = Math.max(0.15, val / maxVal);
                      return (
                        <td key={ci} className="py-1.5 px-1">
                          <div className="w-9 h-9 rounded-lg flex items-center justify-center font-bold mx-auto transition-colors"
                            style={{
                              backgroundColor: isCorrect ? `rgba(99,102,241,${opacity})` : val > 0 ? `rgba(239,68,68,${opacity * 0.5})` : '#f8fafc',
                              color: isCorrect ? (opacity > 0.5 ? '#fff' : '#4338ca') : val > 0 ? '#dc2626' : '#cbd5e1',
                            }}>
                            {val}
                          </div>
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
            <p className="text-xs text-slate-400 text-center mt-2">Blue = correct prediction · Red = misclassification</p>
          </div>
        </div>
      </div>

      <div className="flex items-start gap-2.5 p-4 bg-blue-50 border border-blue-200 rounded-xl">
        <Info className="w-4 h-4 text-blue-500 flex-shrink-0 mt-0.5" />
        <p className="text-xs text-blue-700">
          Model performance reflects evaluation on the synthetic test dataset and should not be interpreted as clinical diagnostic accuracy.
          Metrics will improve when trained on validated public datasets (PhysioNet GaitPDB, UCI HAR).
        </p>
      </div>
    </Layout>
  );
}
