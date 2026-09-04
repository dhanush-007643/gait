import React, { useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard, Upload, Activity, BarChart2, History,
  FileText, Users, Cpu, Settings, HelpCircle, LogOut,
  Zap, Menu, X,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import clsx from 'clsx';

const NAV_ITEMS = [
  { to: '/',           label: 'Dashboard',        icon: LayoutDashboard },
  { to: '/upload',     label: 'Upload Data',       icon: Upload },
  { to: '/monitoring', label: 'Live Monitoring',   icon: Activity },
  { to: '/analysis',   label: 'Analysis',          icon: BarChart2 },
  { to: '/sessions',   label: 'Sessions',          icon: History },
  { to: '/reports',    label: 'Reports',           icon: FileText },
  { to: '/subjects',   label: 'Subjects',          icon: Users },
  { to: '/model',      label: 'Model Performance', icon: Cpu },
];

const BOTTOM_ITEMS = [
  { to: '/settings',   label: 'Settings',          icon: Settings },
  { to: '/help',       label: 'Help & Support',    icon: HelpCircle },
];

interface SidebarProps { className?: string; }

export default function Sidebar({ className }: SidebarProps) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const { logout, user } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => { logout(); navigate('/login'); };

  const SidebarContent = () => (
    <div className="flex flex-col h-full">
      {/* Logo */}
      <div className="flex items-center gap-3 px-4 py-5 border-b border-slate-700/50">
        <div className="w-9 h-9 bg-primary-600 rounded-xl flex items-center justify-center flex-shrink-0">
          <Zap className="w-5 h-5 text-white" />
        </div>
        <div>
          <p className="text-white font-bold text-base leading-none">GaitInsight</p>
          <p className="text-slate-400 text-xs mt-0.5">Gait Analysis Platform</p>
        </div>
      </div>

      {/* Main nav */}
      <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto scrollbar-thin">
        <p className="text-slate-500 text-xs font-semibold uppercase tracking-wider px-3 mb-2">Main Menu</p>
        {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            onClick={() => setMobileOpen(false)}
            className={({ isActive }) => clsx('sidebar-link', isActive && 'active')}
            aria-label={label}
          >
            <Icon className="w-4 h-4 flex-shrink-0" />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>

      {/* Bottom nav */}
      <div className="px-3 pb-3 space-y-0.5 border-t border-slate-700/50 pt-3">
        {BOTTOM_ITEMS.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            onClick={() => setMobileOpen(false)}
            className={({ isActive }) => clsx('sidebar-link', isActive && 'active')}
          >
            <Icon className="w-4 h-4 flex-shrink-0" />
            <span>{label}</span>
          </NavLink>
        ))}
        <button
          onClick={handleLogout}
          className="sidebar-link w-full text-left hover:text-red-400"
          aria-label="Logout"
        >
          <LogOut className="w-4 h-4 flex-shrink-0" />
          <span>Logout</span>
        </button>
      </div>

      {/* User info */}
      {user && (
        <div className="px-3 pb-4">
          <div className="flex items-center gap-2.5 px-3 py-2.5 bg-slate-800 rounded-lg">
            <div className="w-8 h-8 rounded-full bg-primary-600 flex items-center justify-center flex-shrink-0">
              <span className="text-white text-xs font-bold">{user.name.charAt(0)}</span>
            </div>
            <div className="min-w-0">
              <p className="text-white text-xs font-semibold truncate">{user.name}</p>
              <p className="text-slate-400 text-xs capitalize">{user.role}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  return (
    <>
      {/* Mobile hamburger button */}
      <button
        className="lg:hidden fixed top-4 left-4 z-50 w-10 h-10 bg-sidebar rounded-xl flex items-center justify-center text-white shadow-lg"
        onClick={() => setMobileOpen(v => !v)}
        aria-label="Toggle menu"
      >
        {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
      </button>

      {/* Mobile overlay */}
      {mobileOpen && (
        <div
          className="lg:hidden fixed inset-0 bg-black/50 z-40"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Mobile sidebar */}
      <aside className={clsx(
        'lg:hidden fixed top-0 left-0 h-full w-64 bg-sidebar z-50 transform transition-transform duration-300',
        mobileOpen ? 'translate-x-0' : '-translate-x-full'
      )}>
        <SidebarContent />
      </aside>

      {/* Desktop sidebar */}
      <aside className={clsx('hidden lg:flex flex-col w-60 bg-sidebar h-screen sticky top-0 flex-shrink-0', className)}>
        <SidebarContent />
      </aside>
    </>
  );
}
