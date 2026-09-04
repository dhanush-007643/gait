import React, { useState } from 'react';
import { Bell, ChevronDown, Settings, LogOut, FlaskConical } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { isMockMode } from '../../services/api';
import clsx from 'clsx';

interface HeaderProps {
  title: string;
  subtitle?: string;
}

export default function Header({ title, subtitle }: HeaderProps) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [dropdownOpen, setDropdownOpen] = useState(false);

  const handleLogout = () => { logout(); navigate('/login'); };

  return (
    <header className="bg-white border-b border-slate-100 px-6 py-4 flex items-center justify-between gap-4 sticky top-0 z-30">
      {/* Title — offset for mobile hamburger */}
      <div className="ml-10 lg:ml-0">
        <h1 className="text-xl font-bold text-slate-900">{title}</h1>
        {subtitle && <p className="text-sm text-slate-500 mt-0.5">{subtitle}</p>}
      </div>

      <div className="flex items-center gap-3 flex-shrink-0">
        {/* Demo mode badge */}
        {isMockMode && (
          <span className="hidden sm:flex items-center gap-1.5 px-3 py-1 bg-amber-50 border border-amber-200 text-amber-700 text-xs font-semibold rounded-full">
            <FlaskConical className="w-3.5 h-3.5" />
            Demo Mode
          </span>
        )}

        {/* Notification bell */}
        <button
          className="relative w-9 h-9 flex items-center justify-center rounded-lg hover:bg-slate-50 text-slate-500 hover:text-slate-700 transition-colors"
          aria-label="Notifications"
        >
          <Bell className="w-5 h-5" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-primary-500 rounded-full" />
        </button>

        {/* User dropdown */}
        <div className="relative">
          <button
            className="flex items-center gap-2 px-2 py-1.5 rounded-lg hover:bg-slate-50 transition-colors"
            onClick={() => setDropdownOpen(v => !v)}
            aria-expanded={dropdownOpen}
            aria-haspopup="true"
          >
            <div className="w-8 h-8 rounded-full bg-primary-600 flex items-center justify-center">
              <span className="text-white text-xs font-bold">{user?.name?.charAt(0) ?? 'U'}</span>
            </div>
            <div className="hidden sm:block text-left">
              <p className="text-sm font-semibold text-slate-800 leading-none">{user?.name ?? 'User'}</p>
              <p className="text-xs text-slate-500 capitalize mt-0.5">{user?.role ?? 'researcher'}</p>
            </div>
            <ChevronDown className={clsx('w-4 h-4 text-slate-400 transition-transform hidden sm:block', dropdownOpen && 'rotate-180')} />
          </button>

          {dropdownOpen && (
            <>
              <div className="fixed inset-0 z-40" onClick={() => setDropdownOpen(false)} />
              <div className="absolute right-0 mt-2 w-48 bg-white rounded-xl shadow-lg border border-slate-100 py-1.5 z-50">
                <button onClick={() => { navigate('/settings'); setDropdownOpen(false); }}
                  className="flex items-center gap-2.5 w-full px-4 py-2 text-sm text-slate-700 hover:bg-slate-50">
                  <Settings className="w-4 h-4 text-slate-400" /> Profile & Settings
                </button>
                <hr className="my-1 border-slate-100" />
                <button onClick={handleLogout}
                  className="flex items-center gap-2.5 w-full px-4 py-2 text-sm text-red-600 hover:bg-red-50">
                  <LogOut className="w-4 h-4" /> Sign Out
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
