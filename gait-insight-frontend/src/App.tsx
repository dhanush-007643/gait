import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import LoadingState from './components/ui/LoadingState';

// Pages
import Login           from './pages/Login';
import Register        from './pages/Register';
import Dashboard       from './pages/Dashboard';
import UploadData      from './pages/UploadData';
import LiveMonitoring  from './pages/LiveMonitoring';
import Analysis        from './pages/Analysis';
import Sessions        from './pages/Sessions';
import SessionDetail   from './pages/SessionDetail';
import Reports         from './pages/Reports';
import Subjects        from './pages/Subjects';
import ModelPerformance from './pages/ModelPerformance';
import Settings        from './pages/Settings';
import HelpSupport     from './pages/HelpSupport';

// Protected route wrapper
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();
  if (isLoading) return <LoadingState message="Authenticating..." />;
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

// Public route wrapper (redirects to dashboard if already logged in)
function PublicRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();
  if (isLoading) return <LoadingState message="Loading..." />;
  if (isAuthenticated) return <Navigate to="/" replace />;
  return <>{children}</>;
}

function AppRoutes() {
  return (
    <Routes>
      {/* Public */}
      <Route path="/login"    element={<PublicRoute><Login /></PublicRoute>} />
      <Route path="/register" element={<PublicRoute><Register /></PublicRoute>} />

      {/* Protected */}
      <Route path="/"           element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
      <Route path="/upload"     element={<ProtectedRoute><UploadData /></ProtectedRoute>} />
      <Route path="/monitoring" element={<ProtectedRoute><LiveMonitoring /></ProtectedRoute>} />
      <Route path="/analysis"   element={<ProtectedRoute><Analysis /></ProtectedRoute>} />
      <Route path="/analysis/:id" element={<ProtectedRoute><Analysis /></ProtectedRoute>} />
      <Route path="/sessions"   element={<ProtectedRoute><Sessions /></ProtectedRoute>} />
      <Route path="/sessions/:id" element={<ProtectedRoute><SessionDetail /></ProtectedRoute>} />
      <Route path="/reports"    element={<ProtectedRoute><Reports /></ProtectedRoute>} />
      <Route path="/reports/:id" element={<ProtectedRoute><Reports /></ProtectedRoute>} />
      <Route path="/subjects"   element={<ProtectedRoute><Subjects /></ProtectedRoute>} />
      <Route path="/model"      element={<ProtectedRoute><ModelPerformance /></ProtectedRoute>} />
      <Route path="/settings"   element={<ProtectedRoute><Settings /></ProtectedRoute>} />
      <Route path="/help"       element={<ProtectedRoute><HelpSupport /></ProtectedRoute>} />

      {/* Fallback */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  );
}
