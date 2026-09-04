import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Eye, EyeOff, Zap, Activity, Loader2, AlertCircle, FlaskConical } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { isMockMode } from '../services/api';

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail]       = useState(isMockMode ? 'demo@gaitinsight.dev' : '');
  const [password, setPassword] = useState(isMockMode ? 'demo1234' : '');
  const [showPwd, setShowPwd]   = useState(false);
  const [remember, setRemember] = useState(false);
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    const cleanEmail = email.trim().toLowerCase();
    try {
      await login({ email: cleanEmail, password });
      navigate('/');
    } catch (err: any) {
      if (err?.code === 'ERR_NETWORK' || !err?.response) {
        setError('Cannot reach the backend server. If using Render free tier, the service may take 30-50 seconds to spin up from sleep. Please wait a few seconds and try again.');
      } else {
        setError(err?.response?.data?.detail ?? err?.response?.data?.error ?? 'Login failed. Please check your credentials.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex">
      {/* Left panel */}
      <div className="flex-1 flex items-center justify-center p-8 bg-white">
        <div className="w-full max-w-md">
          {/* Logo */}
          <div className="flex items-center gap-3 mb-8">
            <div className="w-10 h-10 bg-primary-600 rounded-xl flex items-center justify-center">
              <Zap className="w-6 h-6 text-white" />
            </div>
            <div>
              <p className="text-xl font-bold text-slate-900">GaitInsight</p>
              <p className="text-xs text-slate-500">Real-Time Gait Monitoring & Pattern Analysis</p>
            </div>
          </div>

          <h2 className="text-2xl font-bold text-slate-900 mb-1">Welcome back</h2>
          <p className="text-slate-500 text-sm mb-8">Sign in to your research account</p>

          {/* Demo mode / credentials helper */}
          <div className="flex items-center justify-between p-3 bg-slate-50 border border-slate-200 rounded-xl mb-6">
            <div className="flex items-center gap-2">
              <FlaskConical className="w-4 h-4 text-primary-600 flex-shrink-0" />
              <div>
                <p className="text-xs font-semibold text-slate-700">Demo Credentials</p>
                <p className="text-[11px] text-slate-500 font-mono">demo@gaitinsight.dev / demo1234</p>
              </div>
            </div>
            <button
              type="button"
              onClick={() => { setEmail('demo@gaitinsight.dev'); setPassword('demo1234'); setError(''); }}
              className="text-xs text-primary-600 hover:text-primary-700 font-medium px-2.5 py-1 bg-white border border-slate-200 hover:border-primary-300 rounded-lg shadow-sm transition-all"
            >
              Fill Demo
            </button>
          </div>

          {error && (
            <div className="flex items-center gap-2 p-3.5 bg-red-50 border border-red-200 rounded-xl mb-5 text-sm text-red-700">
              <AlertCircle className="w-4 h-4 flex-shrink-0" /> {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="email" className="label">Email address</label>
              <input id="email" type="email" className="input" placeholder="you@institution.edu"
                value={email} onChange={e => setEmail(e.target.value)} required autoComplete="email" />
            </div>
            <div>
              <label htmlFor="password" className="label">Password</label>
              <div className="relative">
                <input id="password" type={showPwd ? 'text' : 'password'} className="input pr-10"
                  placeholder="Enter your password" value={password}
                  onChange={e => setPassword(e.target.value)} required autoComplete="current-password" />
                <button type="button" onClick={() => setShowPwd(v => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                  aria-label={showPwd ? 'Hide password' : 'Show password'}>
                  {showPwd ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <label className="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" className="rounded border-slate-300 text-primary-600"
                  checked={remember} onChange={e => setRemember(e.target.checked)} />
                <span className="text-sm text-slate-600">Remember me</span>
              </label>
              <a href="#" className="text-sm text-primary-600 hover:text-primary-700 font-medium">Forgot password?</a>
            </div>
            <button type="submit" className="btn-primary w-full justify-center py-2.5" disabled={loading}>
              {loading ? <><Loader2 className="w-4 h-4 animate-spin" /> Signing in...</> : 'Sign In'}
            </button>
          </form>

          <p className="text-sm text-center text-slate-500 mt-6">
            Don't have an account?{' '}
            <Link to="/register" className="text-primary-600 hover:text-primary-700 font-medium">Create account</Link>
          </p>

          <p className="text-xs text-center text-slate-400 mt-8 leading-relaxed">
            This application is a research/educational prototype for gait pattern analysis.<br />
            It is not a medical diagnostic device.
          </p>
        </div>
      </div>

      {/* Right panel — visual */}
      <div className="hidden lg:flex flex-col flex-1 bg-gradient-to-br from-primary-600 via-primary-700 to-slate-900 p-12 justify-between">
        <div className="flex items-center gap-3 text-white/80">
          <Activity className="w-5 h-5" />
          <span className="text-sm font-medium">B.Tech Biotechnology Capstone Project</span>
        </div>
        <div className="text-white space-y-6">
          <h3 className="text-3xl font-bold leading-tight">
            Wearable Sensor-Based<br />Real-Time Monitoring &<br />Gait Classification
          </h3>
          <p className="text-white/70 text-sm leading-relaxed max-w-sm">
            Analyse human gait patterns using wearable IMU sensors and machine learning.
            Classify Normal, Parkinsonian, Hemiplegic, Ataxic, Spastic, and Antalgic gait patterns.
          </p>
          <div className="grid grid-cols-2 gap-4">
            {[
              { label: 'Gait Classes', value: '6' },
              { label: 'Features Extracted', value: '16+' },
              { label: 'ML Algorithm', value: 'Random Forest' },
              { label: 'Course', value: 'HAP' },
            ].map(({ label, value }) => (
              <div key={label} className="bg-white/10 rounded-xl p-4 backdrop-blur-sm">
                <p className="text-white font-bold text-xl">{value}</p>
                <p className="text-white/60 text-xs mt-0.5">{label}</p>
              </div>
            ))}
          </div>
        </div>
        <p className="text-white/40 text-xs">Human Anatomy and Physiology — Academic Research Platform</p>
      </div>
    </div>
  );
}
