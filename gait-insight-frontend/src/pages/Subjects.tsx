import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, History } from 'lucide-react';
import Layout from '../components/layout/Layout';
import GaitBadge from '../components/ui/GaitBadge';
import LoadingState from '../components/ui/LoadingState';
import EmptyState from '../components/ui/EmptyState';
import ErrorState from '../components/ui/ErrorState';
import { subjectsApi } from '../services/api';
import type { Subject, GaitClass } from '../types';

export default function Subjects() {
  const navigate  = useNavigate();
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [filtered, setFiltered] = useState<Subject[]>([]);
  const [search, setSearch]     = useState('');
  const [loading, setLoading]   = useState(true);
  const [error, setError]       = useState('');

  useEffect(() => {
    (async () => {
      try { const d = await subjectsApi.getAll(); setSubjects(d); setFiltered(d); }
      catch { setError('Unable to load subjects.'); }
      finally { setLoading(false); }
    })();
  }, []);

  useEffect(() => {
    const q = search.toLowerCase();
    setFiltered(subjects.filter(s =>
      s.subject_id.toLowerCase().includes(q) || (s.age_group ?? '').toLowerCase().includes(q)
    ));
  }, [search, subjects]);

  return (
    <Layout title="Subjects" subtitle="Manage research subjects identified by Subject ID only">
      <div className="mb-5 card p-4">
        <div className="relative max-w-xs">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input className="input pl-9" placeholder="Search subject ID or age group..."
            value={search} onChange={e => setSearch(e.target.value)} />
        </div>
        <p className="text-xs text-amber-700 bg-amber-50 px-3 py-2 rounded-lg mt-3 border border-amber-200">
          Subjects are identified by Subject ID only. No personally identifiable information is stored.
        </p>
      </div>

      <div className="card overflow-hidden">
        {loading ? <LoadingState /> : error ? <ErrorState message={error} /> : filtered.length === 0 ? (
          <EmptyState title="No subjects found" message="No subjects match your search." />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-100">
                  {['Subject ID','Age Group','Sex','Sessions','Last Session','Latest Gait Class','Actions'].map(h => (
                    <th key={h} className="text-left px-4 py-3 text-xs font-semibold text-slate-500">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filtered.map(s => (
                  <tr key={s.subject_id} className="border-b border-slate-50 hover:bg-slate-50 transition-colors">
                    <td className="px-4 py-3 font-mono text-sm font-semibold text-primary-600">{s.subject_id}</td>
                    <td className="px-4 py-3 text-slate-600">{s.age_group}</td>
                    <td className="px-4 py-3 text-slate-500">{s.sex ?? '—'}</td>
                    <td className="px-4 py-3">
                      <span className="inline-flex items-center gap-1 text-sm font-semibold text-slate-700">
                        <History className="w-3.5 h-3.5 text-slate-400" /> {s.session_count}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-slate-500 text-xs">{s.last_session}</td>
                    <td className="px-4 py-3">
                      {s.latest_gait_class ? <GaitBadge gaitClass={s.latest_gait_class as GaitClass} size="sm" /> : '—'}
                    </td>
                    <td className="px-4 py-3">
                      <button
                        onClick={() => navigate(`/sessions?subject=${s.subject_id}`)}
                        className="text-xs text-primary-600 hover:text-primary-700 font-medium flex items-center gap-1">
                        <History className="w-3.5 h-3.5" /> View History
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </Layout>
  );
}
