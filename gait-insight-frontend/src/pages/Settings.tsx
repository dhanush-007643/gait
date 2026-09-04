import React, { useState } from 'react';
import { User, Bell, Lock, Monitor, Save, CheckCircle } from 'lucide-react';
import Layout from '../components/layout/Layout';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';

type Tab = 'profile' | 'preferences' | 'security';

export default function Settings() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [tab, setTab]     = useState<Tab>('profile');
  const [saved, setSaved] = useState(false);
  const [form, setForm]   = useState({ name: user?.name ?? '', email: user?.email ?? '', role: user?.role ?? '' });
  const [prefs, setPrefs] = useState({ theme: 'light', notifications: true, units: 'metric' });

  const handleSave = () => { setSaved(true); setTimeout(() => setSaved(false), 2500); };

  const TABS: { key: Tab; label: string; icon: React.ReactNode }[] = [
    { key: 'profile',     label: 'Profile',      icon: <User className="w-4 h-4" /> },
    { key: 'preferences', label: 'Preferences',  icon: <Monitor className="w-4 h-4" /> },
    { key: 'security',    label: 'Security',      icon: <Lock className="w-4 h-4" /> },
  ];

  return (
    <Layout title="Settings" subtitle="Manage your account and preferences">
      <div className="max-w-2xl mx-auto">
        {/* Tabs */}
        <div className="flex gap-1 p-1 bg-slate-100 rounded-xl mb-6">
          {TABS.map(({ key, label, icon }) => (
            <button key={key} onClick={() => setTab(key)}
              className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-lg text-sm font-medium transition-all
                ${tab === key ? 'bg-white shadow text-slate-800' : 'text-slate-500 hover:text-slate-700'}`}>
              {icon} {label}
            </button>
          ))}
        </div>

        {tab === 'profile' && (
          <div className="card p-6 space-y-4">
            <h2 className="font-semibold text-slate-800">Profile Information</h2>
            {saved && (
              <div className="flex items-center gap-2 p-3 bg-green-50 border border-green-200 rounded-xl text-sm text-green-700">
                <CheckCircle className="w-4 h-4" /> Profile saved successfully.
              </div>
            )}
            <div><label className="label">Full Name</label>
              <input className="input" value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} /></div>
            <div><label className="label">Email Address</label>
              <input className="input" type="email" value={form.email} onChange={e => setForm(f => ({ ...f, email: e.target.value }))} /></div>
            <div><label className="label">Role</label>
              <input className="input bg-slate-50" value={form.role} disabled /></div>
            <button className="btn-primary" onClick={handleSave}><Save className="w-4 h-4" /> Save Changes</button>
          </div>
        )}

        {tab === 'preferences' && (
          <div className="card p-6 space-y-5">
            <h2 className="font-semibold text-slate-800">Preferences</h2>
            <div>
              <label className="label">Theme</label>
              <select className="input" value={prefs.theme} onChange={e => setPrefs(p => ({ ...p, theme: e.target.value }))}>
                <option value="light">Light</option>
                <option value="dark">Dark (coming soon)</option>
              </select>
            </div>
            <div>
              <label className="label">Units</label>
              <select className="input" value={prefs.units} onChange={e => setPrefs(p => ({ ...p, units: e.target.value }))}>
                <option value="metric">Metric (m, m/s, steps/min)</option>
                <option value="imperial">Imperial</option>
              </select>
            </div>
            <label className="flex items-center gap-3 cursor-pointer">
              <div className={`relative w-10 h-6 rounded-full transition-colors ${prefs.notifications ? 'bg-primary-600' : 'bg-slate-200'}`}
                onClick={() => setPrefs(p => ({ ...p, notifications: !p.notifications }))}>
                <span className={`absolute top-1 left-1 w-4 h-4 bg-white rounded-full shadow transition-transform ${prefs.notifications ? 'translate-x-4' : ''}`} />
              </div>
              <span className="text-sm text-slate-700 flex items-center gap-2"><Bell className="w-4 h-4 text-slate-400" /> Email Notifications</span>
            </label>
            <button className="btn-primary" onClick={handleSave}><Save className="w-4 h-4" /> Save Preferences</button>
          </div>
        )}

        {tab === 'security' && (
          <div className="card p-6 space-y-5">
            <h2 className="font-semibold text-slate-800">Security</h2>
            <div><label className="label">Current Password</label><input type="password" className="input" placeholder="••••••••" /></div>
            <div><label className="label">New Password</label><input type="password" className="input" placeholder="••••••••" /></div>
            <div><label className="label">Confirm New Password</label><input type="password" className="input" placeholder="••••••••" /></div>
            <button className="btn-primary"><Lock className="w-4 h-4" /> Update Password</button>
            <hr className="border-slate-100" />
            <div>
              <p className="font-medium text-slate-700 text-sm mb-1">Sign Out Everywhere</p>
              <p className="text-xs text-slate-500 mb-3">Signs you out from all active sessions across all devices.</p>
              <button className="btn-danger" onClick={() => { logout(); navigate('/login'); }}>Sign Out All Sessions</button>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
}
