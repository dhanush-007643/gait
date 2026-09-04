import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Eye, EyeOff, Zap, Loader2, AlertCircle, CheckCircle } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import type { UserRole } from '../types';

function PasswordStrength({ pwd }: { pwd: string }) {
  const checks = [pwd.length >= 8, /[A-Z]/.test(pwd), /[0-9]/.test(pwd), /[^A-Za-z0-9]/.test(pwd)];
  const score = checks.filter(Boolean).length;
  const label = ['', 'Weak', 'Fair', 'Good', 'Strong'][score];
  const colors = ['', 'bg-red-500', 'bg-orange-400', 'bg-yellow-400', 'bg-green-500'];
  return (
    <div className="mt-2">
      <div className="flex gap-1 mb-1">
        {[1,2,3,4].map(i => (
          <div key={i} className={`h-1 flex-1 rounded-full transition-colors ${i <= score ? colors[score] : 'bg-slate-200'}`} />
        ))}
      </div>
      {pwd && <p className="text-xs text-slate-500">Strength: <span className="font-medium">{label}</span></p>}
    </div>
  );
}

export default function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ name: '', email: '', password: '', confirm: '', role: 'researcher' as UserRole });
  const [showPwd, setShowPwd] = useState(false);
  const [agreed, setAgreed]   = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState('');
  const [success, setSuccess] = useState(false);

  const set = (k: string, v: string) => setForm(f => ({ ...f, [k]: v }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    if (form.password !== form.confirm) { setError('Passwords do not match.'); return; }
    if (form.password.length < 8) { setError('Password must contain at least 8 characters.'); return; }
    if (!agreed) { setError('Please accept the terms of use.'); return; }
    setLoading(true);
    const cleanEmail = form.email.trim().toLowerCase();
    const cleanName = form.name.trim();
    try {
      await register({ name: cleanName, email: cleanEmail, password: form.password, role: form.role });
      setSuccess(true);
      setTimeout(() => navigate('/login'), 1800);
    } catch (err: any) {
      if (err?.code === 'ERR_NETWORK' || !err?.response) {
        setError('Cannot reach the backend server. If using Render free tier, the service may take 30-50 seconds to spin up from sleep. Please wait a few seconds and try again.');
      } else {
        setError(err?.response?.data?.detail ?? err?.response?.data?.error ?? 'Registration failed. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-6 bg-slate-50">
      <div className="w-full max-w-lg">
        <div className="card p-8">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-9 h-9 bg-primary-600 rounded-xl flex items-center justify-center">
              <Zap className="w-5 h-5 text-white" />
            </div>
            <p className="text-lg font-bold text-slate-900">GaitInsight</p>
          </div>
          <h2 className="text-xl font-bold text-slate-900 mb-1">Create your account</h2>
          <p className="text-slate-500 text-sm mb-6">Join the gait research platform</p>

          {success ? (
            <div className="flex flex-col items-center gap-3 py-8 text-center">
              <CheckCircle className="w-12 h-12 text-green-500" />
              <p className="font-semibold text-slate-800">Account created successfully!</p>
              <p className="text-sm text-slate-500">Redirecting to login...</p>
            </div>
          ) : (
            <>
              {error && (
                <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-xl mb-4 text-sm text-red-700">
                  <AlertCircle className="w-4 h-4 flex-shrink-0" /> {error}
                </div>
              )}
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label htmlFor="name" className="label">Full Name</label>
                  <input id="name" type="text" className="input" placeholder="Dr. Arjun Sharma"
                    value={form.name} onChange={e => set('name', e.target.value)} required />
                </div>
                <div>
                  <label htmlFor="reg-email" className="label">Email address</label>
                  <input id="reg-email" type="email" className="input" placeholder="you@institution.edu"
                    value={form.email} onChange={e => set('email', e.target.value)} required />
                </div>
                <div>
                  <label htmlFor="role" className="label">Role</label>
                  <select id="role" className="input" value={form.role} onChange={e => set('role', e.target.value)}>
                    <option value="researcher">Researcher</option>
                    <option value="clinician">Clinician</option>
                    <option value="student">Student</option>
                    <option value="admin">Admin</option>
                  </select>
                </div>
                <div>
                  <label htmlFor="reg-password" className="label">Password</label>
                  <div className="relative">
                    <input id="reg-password" type={showPwd ? 'text' : 'password'} className="input pr-10"
                      value={form.password} onChange={e => set('password', e.target.value)} required />
                    <button type="button" onClick={() => setShowPwd(v => !v)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600" aria-label="Toggle password">
                      {showPwd ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                  <PasswordStrength pwd={form.password} />
                </div>
                <div>
                  <label htmlFor="confirm" className="label">Confirm Password</label>
                  <input id="confirm" type="password" className="input"
                    value={form.confirm} onChange={e => set('confirm', e.target.value)} required />
                </div>
                <label className="flex items-start gap-2 cursor-pointer">
                  <input type="checkbox" className="mt-0.5 rounded border-slate-300 text-primary-600"
                    checked={agreed} onChange={e => setAgreed(e.target.checked)} />
                  <span className="text-xs text-slate-600 leading-relaxed">
                    I confirm this platform is for research/educational use only and is not a medical diagnostic tool.
                  </span>
                </label>
                <button type="submit" className="btn-primary w-full justify-center py-2.5" disabled={loading}>
                  {loading ? <><Loader2 className="w-4 h-4 animate-spin" /> Creating account...</> : 'Create Account'}
                </button>
              </form>
            </>
          )}
          <p className="text-sm text-center text-slate-500 mt-6">
            Already have an account?{' '}
            <Link to="/login" className="text-primary-600 hover:text-primary-700 font-medium">Sign in</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
