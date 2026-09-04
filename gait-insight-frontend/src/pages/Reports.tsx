import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Printer, Download, Zap, Info } from 'lucide-react';
import Layout from '../components/layout/Layout';
import GaitBadge from '../components/ui/GaitBadge';
import SensorChart from '../components/ui/SensorChart';
import LoadingState from '../components/ui/LoadingState';
import ErrorState from '../components/ui/ErrorState';
import { sessionsApi } from '../services/api';
import { generateSensorPoints, GAIT_COLORS_MAP } from '../data/mockData';
import type { SessionDetail as SD, GaitClass } from '../types';

const SECTIONS = ['Session Information','Gait Parameters','Sensor Data Overview','Graphical Analysis','Machine Learning Prediction','Model Information','Disclaimer'];

export default function Reports() {
  const { id } = useParams<{ id?: string }>();
  const navigate = useNavigate();
  const [detail, setDetail] = useState<SD|null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    (async () => {
      setLoading(true);
      setError('');
      try {
        let targetId = id;
        if (!targetId) {
          const all = await sessionsApi.getAll({ per_page: 1 });
          if (all.items && all.items.length > 0) {
            targetId = all.items[0].session_id;
          } else {
            setError('No recorded gait sessions found. Please upload a CSV file to generate a report.');
            setLoading(false);
            return;
          }
        }
        const data = await sessionsApi.getById(targetId);
        setDetail(data);
      } catch (e: any) {
        setError(e?.response?.data?.error ?? e?.message ?? 'Report not found.');
      } finally {
        setLoading(false);
      }
    })();
  }, [id]);

  if (loading) return <Layout title="Report"><LoadingState message="Loading report..." /></Layout>;
  if (error || !detail) return <Layout title="Report"><ErrorState message={error} /></Layout>;

  const { session, features, prediction } = detail;
  const predClass = (prediction?.predicted_class ?? 'normal') as GaitClass;
  const color = GAIT_COLORS_MAP[predClass] || '#22c55e';
  const sensorData = generateSensorPoints(200, predClass);

  const formatDate = (d?: string) => {
    if (!d) return '—';
    try {
      const parsed = new Date(d.includes(' ') && !d.includes('T') ? d.replace(' ', 'T') : d);
      return isNaN(parsed.getTime()) ? d : parsed.toLocaleDateString();
    } catch {
      return d;
    }
  };

  return (
    <Layout title="Gait Analysis Report">
      {/* Actions */}
      <div className="flex flex-wrap items-center justify-between gap-3 mb-5 print:hidden">
        <button onClick={() => navigate(-1)} className="btn-secondary text-xs py-1.5 px-3">
          <ArrowLeft className="w-3.5 h-3.5" /> Back
        </button>
        <div className="flex gap-2">
          <button onClick={() => window.print()} className="btn-secondary text-xs py-1.5 px-3">
            <Printer className="w-3.5 h-3.5" /> Print
          </button>
          <button onClick={() => window.print()} className="btn-primary text-xs py-1.5 px-3">
            <Download className="w-3.5 h-3.5" /> Download PDF
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-5">
        {/* Table of contents */}
        <div className="card p-5 print:hidden">
          <h3 className="font-semibold text-slate-800 mb-3 text-sm">Report Contents</h3>
          <ol className="space-y-1.5">
            {SECTIONS.map((s, i) => (
              <li key={s} className="flex items-center gap-2 text-xs text-slate-600 hover:text-primary-600 cursor-pointer">
                <span className="w-5 h-5 bg-primary-50 text-primary-600 rounded font-bold flex items-center justify-center flex-shrink-0 text-xs">{i+1}</span>
                {s}
              </li>
            ))}
          </ol>
        </div>

        {/* Report body */}
        <div className="lg:col-span-3 space-y-5">
          {/* Header */}
          <div className="card p-6">
            <div className="flex items-center justify-between mb-5 pb-5 border-b border-slate-100">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-primary-600 rounded-xl flex items-center justify-center">
                  <Zap className="w-6 h-6 text-white" />
                </div>
                <div>
                  <p className="font-bold text-slate-900">GaitInsight</p>
                  <p className="text-xs text-slate-500">Gait Analysis Report</p>
                </div>
              </div>
              <div className="text-right text-xs text-slate-500">
                <p>Session: <span className="font-semibold">{session.session_id}</span></p>
                <p className="mt-0.5">{formatDate(session.session_date)}</p>
              </div>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              {[
                { label: 'Subject ID', value: session.subject_id },
                { label: 'Duration',   value: `${session.duration_seconds}s` },
                { label: 'Condition',  value: session.walking_condition },
                { label: 'Data Source',value: (session.data_source || '').replace('_', ' ') },
              ].map(({ label, value }) => (
                <div key={label}>
                  <p className="text-xs text-slate-500">{label}</p>
                  <p className="font-semibold text-slate-800 text-sm mt-0.5">{value}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Results summary */}
          <div className="card p-5">
            <h3 className="font-semibold text-slate-800 mb-4">Results Summary</h3>
            {prediction ? (
              <div className="flex items-center gap-6">
                <div>
                  <p className="text-xs text-slate-500">Predicted Gait</p>
                  <GaitBadge gaitClass={predClass} size="lg" />
                </div>
                <div>
                  <p className="text-xs text-slate-500">Confidence Score</p>
                  <p className="text-2xl font-extrabold" style={{ color }}>{((prediction.confidence_score ?? 0) * 100).toFixed(1)}%</p>
                </div>
                <div>
                  <p className="text-xs text-slate-500">Model</p>
                  <p className="font-semibold text-slate-700 text-sm">{prediction.model_name || 'Random Forest'}</p>
                </div>
                <div>
                  <p className="text-xs text-slate-500">Model Version</p>
                  <p className="font-semibold text-slate-700 text-sm">{prediction.model_version || '1.0.0'}</p>
                </div>
              </div>
            ) : (
              <p className="text-sm text-slate-400">No prediction recorded for this session.</p>
            )}
          </div>

          {/* Parameters */}
          <div className="card p-5">
            <h3 className="font-semibold text-slate-800 mb-3">Gait Parameters</h3>
            {features ? (
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                {[
                  { l: 'Step Count', v: features.step_count ?? 0, u: 'steps' },
                  { l: 'Cadence',    v: features.cadence ?? 0,    u: 'steps/min' },
                  { l: 'Speed',      v: features.walking_speed ?? 0, u: 'm/s' },
                  { l: 'Step Length',v: features.step_length ?? 0,   u: 'm' },
                  { l: 'Stride',     v: features.stride_length ?? 0, u: 'm' },
                  { l: 'Symmetry',   v: typeof features.gait_symmetry === 'number' ? features.gait_symmetry.toFixed(3) : '0.000', u: 'ratio' },
                ].map(({ l, v, u }) => (
                  <div key={l} className="bg-slate-50 rounded-lg p-3">
                    <p className="text-xs text-slate-500">{l}</p>
                    <p className="font-bold text-slate-800">{v} <span className="text-xs font-normal text-slate-400">{u}</span></p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-slate-400">No parameters recorded.</p>
            )}
          </div>

          {/* Charts */}
          <div className="card p-5">
            <h3 className="font-semibold text-slate-800 mb-3">Graphical Analysis</h3>
            <SensorChart data={sensorData} type="acceleration" height={180} />
          </div>

          {/* Disclaimer */}
          <div className="card p-5 bg-slate-50">
            <div className="flex items-start gap-2">
              <Info className="w-4 h-4 text-slate-400 flex-shrink-0 mt-0.5" />
              <p className="text-xs text-slate-500 leading-relaxed">
                <strong>Disclaimer:</strong> This system is a research/educational prototype for gait pattern analysis and is not a medical diagnostic device.
                This report should not be used in place of professional medical assessment. Gait patterns presented herein are derived from software-based
                signal processing and machine learning, and are intended solely for research and educational purposes.
              </p>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}
