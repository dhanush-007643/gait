import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Download, Tag } from 'lucide-react';
import Layout from '../components/layout/Layout';
import GaitBadge from '../components/ui/GaitBadge';
import SensorChart from '../components/ui/SensorChart';
import LoadingState from '../components/ui/LoadingState';
import ErrorState from '../components/ui/ErrorState';
import ChartCard from '../components/ui/ChartCard';
import { sessionsApi } from '../services/api';
import { generateSensorPoints, GAIT_COLORS_MAP } from '../data/mockData';
import type { SessionDetail as SD, GaitClass } from '../types';

function InfoRow({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="flex justify-between py-2.5 border-b border-slate-50 last:border-0">
      <span className="text-sm text-slate-500">{label}</span>
      <span className="text-sm font-semibold text-slate-800 text-right">{value}</span>
    </div>
  );
}

export default function SessionDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [detail, setDetail] = useState<SD | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState('');

  const load = async () => {
    if (!id) return;
    setLoading(true); setError('');
    try { setDetail(await sessionsApi.getById(id)); }
    catch (e: any) { setError(e?.message ?? 'Session not found.'); }
    finally { setLoading(false); }
  };
  useEffect(() => { load(); }, [id]);

  if (loading) return <Layout title="Session Detail"><LoadingState /></Layout>;
  if (error || !detail) return <Layout title="Session Detail"><ErrorState message={error} onRetry={load} /></Layout>;

  const { session, features, prediction } = detail;
  const predClass = (prediction?.predicted_class ?? 'normal') as GaitClass;
  const color = GAIT_COLORS_MAP[predClass] || '#22c55e';
  const sensorData = generateSensorPoints(200, predClass);

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
    <Layout title="Session Detail">
      <div className="flex flex-wrap items-center justify-between gap-3 mb-5">
        <button onClick={() => navigate('/sessions')} className="btn-secondary text-xs py-1.5 px-3">
          <ArrowLeft className="w-3.5 h-3.5" /> Back to Sessions
        </button>
        <button onClick={() => navigate(`/reports/${session.session_id}`)} className="btn-primary text-xs py-1.5 px-3">
          <Download className="w-3.5 h-3.5" /> Download Report
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 mb-5">
        {/* Session info */}
        <div className="card p-5">
          <h3 className="font-semibold text-slate-800 mb-3 flex items-center gap-2">
            <Tag className="w-4 h-4 text-primary-500" /> Session Information
          </h3>
          <InfoRow label="Session ID" value={session.session_id} />
          <InfoRow label="Subject ID" value={session.subject_id} />
          <InfoRow label="Date" value={formatDate(session.session_date)} />
          <InfoRow label="Duration" value={`${session.duration_seconds}s`} />
          <InfoRow label="Condition" value={session.walking_condition} />
          <InfoRow label="Data Source" value={(session.data_source || '').replace('_', ' ')} />
          {session.file_name && <InfoRow label="File" value={session.file_name} />}
        </div>

        {/* Prediction */}
        <div className="card p-5">
          <h3 className="font-semibold text-slate-800 mb-3">ML Prediction</h3>
          {prediction ? (
            <>
              <div className="flex flex-col items-center py-4">
                <GaitBadge gaitClass={predClass} size="lg" />
                <p className="text-3xl font-extrabold mt-3" style={{ color }}>
                  {((prediction.confidence_score ?? 0) * 100).toFixed(1)}%
                </p>
                <p className="text-xs text-slate-500 mt-1">Confidence Score</p>
                <div className="w-full mt-3 bg-slate-100 rounded-full h-2">
                  <div className="h-2 rounded-full" style={{ width: `${(prediction.confidence_score ?? 0) * 100}%`, backgroundColor: color }} />
                </div>
              </div>
              <InfoRow label="Model" value={prediction.model_name || 'Random Forest'} />
              <InfoRow label="Version" value={prediction.model_version || '1.0.0'} />
              <InfoRow label="Timestamp" value={formatDate(prediction.prediction_timestamp)} />
            </>
          ) : (
            <p className="text-sm text-slate-400 py-8 text-center">No prediction available for this session.</p>
          )}
        </div>

        {/* Features */}
        <div className="card p-5">
          <h3 className="font-semibold text-slate-800 mb-3">Gait Parameters</h3>
          {features ? (
            <>
              <InfoRow label="Step Count" value={features.step_count ?? 0} />
              <InfoRow label="Cadence" value={`${features.cadence ?? 0} steps/min`} />
              <InfoRow label="Walking Speed" value={`${features.walking_speed ?? 0} m/s`} />
              <InfoRow label="Step Length" value={`${features.step_length ?? 0} m`} />
              <InfoRow label="Stride Length" value={`${features.stride_length ?? 0} m`} />
              <InfoRow label="Stance Time" value={`${features.stance_time ?? 0} s`} />
              <InfoRow label="Swing Time" value={`${features.swing_time ?? 0} s`} />
              <InfoRow label="Gait Symmetry" value={typeof features.gait_symmetry === 'number' ? features.gait_symmetry.toFixed(3) : '0.000'} />
            </>
          ) : (
            <p className="text-sm text-slate-400 py-8 text-center">No feature data recorded.</p>
          )}
        </div>
      </div>

      {/* Sensor charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <ChartCard title="Illustrative Acceleration Signal" subtitle="Synthetic example; raw sensor samples are not stored">
          <SensorChart data={sensorData} type="acceleration" height={200} />
        </ChartCard>
        <ChartCard title="Illustrative Gyroscope Signal" subtitle="Synthetic example; raw sensor samples are not stored">
          <SensorChart data={sensorData} type="gyroscope" height={200} />
        </ChartCard>
      </div>
    </Layout>
  );
}
