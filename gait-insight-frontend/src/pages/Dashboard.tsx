import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Activity, TrendingUp, AlertTriangle, Award, Upload,
  History, ChevronRight, Footprints,
} from 'lucide-react';
import {
  PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer,
  LineChart, Line, XAxis, YAxis, CartesianGrid,
} from 'recharts';
import Layout from '../components/layout/Layout';
import StatCard from '../components/ui/StatCard';
import ChartCard from '../components/ui/ChartCard';
import GaitBadge from '../components/ui/GaitBadge';
import LoadingState from '../components/ui/LoadingState';
import ErrorState from '../components/ui/ErrorState';
import { dashboardApi } from '../services/api';
import { generateSensorPoints } from '../data/mockData';
import type { DashboardSummary, GaitClass } from '../types';
import { useAuth } from '../context/AuthContext';

function ParameterCard({ label, value, unit, color }: { label: string; value: string | number; unit: string; color: string }) {
  return (
    <div className="card p-4 hover:shadow-card-md transition-shadow">
      <p className="text-xs text-slate-500 font-medium">{label}</p>
      <p className="text-2xl font-bold mt-1" style={{ color }}>{value}</p>
      <p className="text-xs text-slate-400 mt-0.5">{unit}</p>
    </div>
  );
}

export default function Dashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [data, setData]       = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState('');
  const sensorData = generateSensorPoints(80, 'normal');

  const load = async () => {
    setLoading(true); setError('');
    try { setData(await dashboardApi.getSummary()); }
    catch { setError('Unable to load dashboard data.'); }
    finally { setLoading(false); }
  };
  useEffect(() => { load(); }, []);

  if (loading) return <Layout title="Dashboard"><LoadingState message="Loading dashboard..." /></Layout>;
  if (error || !data) return <Layout title="Dashboard"><ErrorState message={error} onRetry={load} /></Layout>;

  const params = data.latest_features;
  const total = data.total_sessions || 0;
  const normalPct = total > 0 ? Math.round(((data.normal_gait || 0) / total) * 100) : 0;
  const abnormalPct = total > 0 ? Math.round(((data.abnormal_gait || 0) / total) * 100) : 0;
  const avgConf = typeof data.avg_confidence === 'number' ? (data.avg_confidence * 100).toFixed(1) : '92.0';
  const gaitDist = data.gait_distribution ?? [];
  const recentList = data.recent_sessions ?? [];

  return (
    <Layout title="Dashboard" subtitle={`Welcome back, ${user?.name ?? 'Researcher'}. Monitor and track gait patterns in real-time.`}>
      {/* Stat cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <StatCard title="Total Sessions" value={total}
          subtitle={`${data.sessions_this_month ?? total} this month`}
          icon={<Activity className="w-5 h-5 text-primary-600" />} iconBg="bg-primary-50" />
        <StatCard title="Normal Gait" value={data.normal_gait ?? 0}
          subtitle={`${normalPct}%`}
          icon={<TrendingUp className="w-5 h-5 text-green-600" />} iconBg="bg-green-50" />
        <StatCard title="Abnormal Gait" value={data.abnormal_gait ?? 0}
          subtitle={`${abnormalPct}%`}
          icon={<AlertTriangle className="w-5 h-5 text-orange-500" />} iconBg="bg-orange-50" />
        <StatCard title="Avg. Confidence" value={`${avgConf}%`}
          subtitle="Model confidence" icon={<Award className="w-5 h-5 text-primary-600" />} iconBg="bg-primary-50" />
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 mb-5">
        {/* Donut chart */}
        <ChartCard title="Gait Classification Overview" subtitle={`${total} total sessions`}>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie data={gaitDist} cx="50%" cy="50%" innerRadius={55} outerRadius={85}
                paddingAngle={3} dataKey="value">
                {gaitDist.map((entry, i) => (
                  <Cell key={i} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip formatter={(v: any, n: any) => [v, n]} contentStyle={{ borderRadius: '8px', fontSize: '12px' }} />
              <Legend iconType="circle" iconSize={8} wrapperStyle={{ fontSize: '12px' }} />
            </PieChart>
          </ResponsiveContainer>
        </ChartCard>

        {/* Recent activity */}
        <ChartCard title="Recent Activity"
          action={<button onClick={() => navigate('/sessions')} className="text-xs text-primary-600 font-medium flex items-center gap-1 hover:underline">View All <ChevronRight className="w-3 h-3" /></button>}>
          <div className="space-y-2.5 mt-1">
            {recentList.length === 0 ? (
              <p className="text-xs text-slate-400 py-6 text-center">No sessions recorded yet. Upload a CSV to get started.</p>
            ) : (
              recentList.map(s => (
                <div key={s.session_id} onClick={() => navigate(`/sessions/${s.session_id}`)}
                  className="flex items-center gap-3 p-2.5 rounded-lg hover:bg-slate-50 cursor-pointer transition-colors">
                  <div className="w-8 h-8 rounded-lg bg-primary-50 flex items-center justify-center flex-shrink-0">
                    <Footprints className="w-4 h-4 text-primary-600" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-semibold text-slate-700 truncate">{s.session_id}</p>
                    <p className="text-xs text-slate-400">{s.subject_id}</p>
                  </div>
                  <GaitBadge gaitClass={s.gait_class as GaitClass} size="sm" />
                  <span className="text-xs text-slate-400 flex-shrink-0">{s.date}</span>
                </div>
              ))
            )}
          </div>
        </ChartCard>
      </div>

      {/* Gait Parameters */}
      {params && (
        <div className="mb-5">
          <h2 className="text-sm font-semibold text-slate-700 mb-3">Gait Parameters (Latest Session)</h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            <ParameterCard label="Cadence" value={params.cadence} unit="steps/min" color="#6366f1" />
            <ParameterCard label="Walking Speed" value={params.walking_speed} unit="m/s" color="#22c55e" />
            <ParameterCard label="Step Length" value={params.step_length} unit="m" color="#f97316" />
            <ParameterCard label="Stride Length" value={params.stride_length} unit="m" color="#a855f7" />
            <ParameterCard label="Stance Time" value={params.stance_time} unit="sec" color="#ef4444" />
            <ParameterCard label="Swing Time" value={params.swing_time} unit="sec" color="#06b6d4" />
          </div>
        </div>
      )}

      {/* Sensor Activity chart */}
      <ChartCard title="Sensor Activity" subtitle="Simulated acceleration signal (demo)"
        action={
          <div className="flex gap-2">
            <button onClick={() => navigate('/upload')} className="btn-primary text-xs py-1.5 px-3">
              <Upload className="w-3.5 h-3.5" /> Upload
            </button>
            <button onClick={() => navigate('/sessions')} className="btn-secondary text-xs py-1.5 px-3">
              <History className="w-3.5 h-3.5" /> Sessions
            </button>
          </div>
        }>
        <ResponsiveContainer width="100%" height={180}>
          <LineChart data={sensorData.slice(0, 80)} margin={{ top: 4, right: 8, left: -10, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
            <XAxis dataKey="timestamp" tickFormatter={(v: number) => `${v.toFixed(1)}s`} tick={{ fontSize: 10, fill: '#94a3b8' }} tickLine={false} axisLine={false} />
            <YAxis tick={{ fontSize: 10, fill: '#94a3b8' }} tickLine={false} axisLine={false} />
            <Tooltip contentStyle={{ borderRadius: '8px', fontSize: '11px' }} />
            <Legend wrapperStyle={{ fontSize: '11px' }} />
            <Line type="monotone" dataKey="acceleration_x" stroke="#6366f1" strokeWidth={1.5} dot={false} name="Acc X" isAnimationActive={false} />
            <Line type="monotone" dataKey="acceleration_y" stroke="#22c55e" strokeWidth={1.5} dot={false} name="Acc Y" isAnimationActive={false} />
            <Line type="monotone" dataKey="acceleration_z" stroke="#f97316" strokeWidth={1.5} dot={false} name="Acc Z" isAnimationActive={false} />
          </LineChart>
        </ResponsiveContainer>
      </ChartCard>

      {/* Disclaimer */}
      <p className="text-xs text-slate-400 text-center mt-6 leading-relaxed">
        This application is a research/educational prototype for gait pattern analysis.
        It is not a medical diagnostic device and should not replace assessment by a qualified healthcare professional.
      </p>
    </Layout>
  );
}
