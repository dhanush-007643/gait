import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Filter, Eye, Download, Trash2 } from 'lucide-react';
import Layout from '../components/layout/Layout';
import GaitBadge from '../components/ui/GaitBadge';
import LoadingState from '../components/ui/LoadingState';
import EmptyState from '../components/ui/EmptyState';
import ErrorState from '../components/ui/ErrorState';
import Pagination from '../components/ui/Pagination';
import ConfirmationDialog from '../components/ui/ConfirmationDialog';
import { sessionsApi } from '../services/api';
import type { GaitSession, GaitClass } from '../types';

const GAIT_OPTIONS = ['all','normal','parkinsonian','hemiplegic','ataxic','spastic','antalgic'];

export default function Sessions() {
  const navigate = useNavigate();
  const [sessions, setSessions] = useState<GaitSession[]>([]);
  const [total, setTotal]       = useState(0);
  const [page, setPage]         = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [search, setSearch]     = useState('');
  const [gaitFilter, setGait]   = useState('all');
  const [loading, setLoading]   = useState(true);
  const [error, setError]       = useState('');
  const [delId, setDelId]       = useState('');

  useEffect(() => {
    const subject = new URLSearchParams(window.location.search).get('subject');
    if (subject) setSearch(subject);
  }, []);

  const load = async () => {
    setLoading(true); setError('');
    try {
      const res = await sessionsApi.getAll({ page, per_page: 5, gait_class: gaitFilter, search });
      setSessions(res.items); setTotal(res.total); setTotalPages(res.total_pages);
    } catch { setError('Unable to load sessions.'); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, [page, gaitFilter, search]);

  const handleDelete = async () => {
    await sessionsApi.delete(delId);
    setDelId(''); load();
  };

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
    <Layout title="Sessions" subtitle="View and manage your gait analysis sessions">
      {/* Filters */}
      <div className="card p-4 mb-5 flex flex-wrap gap-3 items-center">
        <div className="relative flex-1 min-w-48">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input className="input pl-9" placeholder="Search session ID or subject..."
            value={search} onChange={e => { setSearch(e.target.value); setPage(1); }} />
        </div>
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-slate-400" />
          <select className="input py-2" value={gaitFilter} onChange={e => { setGait(e.target.value); setPage(1); }}>
            {GAIT_OPTIONS.map(o => <option key={o} value={o}>{o === 'all' ? 'All Gait Types' : o.charAt(0).toUpperCase() + o.slice(1)}</option>)}
          </select>
        </div>
        <span className="text-xs text-slate-500">{total} session{total !== 1 ? 's' : ''} found</span>
      </div>

      {/* Table */}
      <div className="card overflow-hidden mb-4">
        {loading ? <LoadingState message="Loading sessions..." /> : error ? <ErrorState message={error} onRetry={load} /> : sessions.length === 0 ? (
          <EmptyState title="No sessions found" message='Try adjusting your search filters or upload a new CSV file.'
            action={<button className="btn-primary" onClick={() => navigate('/upload')}>Upload Data</button>} />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm" role="table">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-100">
                  {['Session ID','Subject ID','Date','Duration','Gait Type','Confidence','Status','Actions'].map(h => (
                    <th key={h} className="text-left px-4 py-3 text-xs font-semibold text-slate-500 whitespace-nowrap">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {sessions.map(s => {
                  const hasPrediction = Boolean(s.predicted_class) && s.confidence_score != null;
                  return (
                    <tr key={s.session_id} className="border-b border-slate-50 hover:bg-slate-50 transition-colors">
                      <td className="px-4 py-3 font-mono text-xs font-semibold text-primary-600">{s.session_id}</td>
                      <td className="px-4 py-3 font-medium text-slate-700">{s.subject_id}</td>
                      <td className="px-4 py-3 text-slate-500 text-xs whitespace-nowrap">{formatDate(s.session_date)}</td>
                      <td className="px-4 py-3 text-slate-500">{s.duration_seconds}s</td>
                      <td className="px-4 py-3">
                        {hasPrediction ? <GaitBadge gaitClass={s.predicted_class as GaitClass} size="sm" /> : <span className="text-slate-300 text-xs">—</span>}
                      </td>
                      <td className="px-4 py-3">
                        {hasPrediction ? (
                          <span className="text-sm font-semibold text-slate-700">{(s.confidence_score! * 100).toFixed(1)}%</span>
                        ) : '—'}
                      </td>
                      <td className="px-4 py-3">
                        <span className={`badge ${s.status === 'completed' ? 'bg-green-50 text-green-700' : 'bg-amber-50 text-amber-700'}`}>
                          {s.status}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-1">
                          <button onClick={() => navigate(`/sessions/${s.session_id}`)}
                            className="w-7 h-7 flex items-center justify-center rounded-lg hover:bg-primary-50 text-slate-400 hover:text-primary-600 transition-colors"
                            aria-label={`View session ${s.session_id}`}>
                            <Eye className="w-3.5 h-3.5" />
                          </button>
                          <button onClick={() => navigate(`/reports/${s.session_id}`)}
                            className="w-7 h-7 flex items-center justify-center rounded-lg hover:bg-green-50 text-slate-400 hover:text-green-600 transition-colors"
                            aria-label={`Download report for ${s.session_id}`}>
                            <Download className="w-3.5 h-3.5" />
                          </button>
                          <button onClick={() => setDelId(s.session_id)}
                            className="w-7 h-7 flex items-center justify-center rounded-lg hover:bg-red-50 text-slate-400 hover:text-red-500 transition-colors"
                            aria-label={`Delete session ${s.session_id}`}>
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Pagination */}
      <div className="flex justify-center">
        <Pagination page={page} totalPages={totalPages} onPageChange={setPage} />
      </div>

      <ConfirmationDialog
        open={!!delId}
        title="Delete Session"
        message={`Delete session ${delId}? This action cannot be undone.`}
        confirmLabel="Delete"
        danger
        onConfirm={handleDelete}
        onCancel={() => setDelId('')}
      />
    </Layout>
  );
}
