// ============================================================
// src/services/api.ts
// API service layer — switches between mock data and real backend
// via VITE_USE_MOCK environment variable.
// ============================================================

import axios from 'axios';
import type {
  LoginRequest, LoginResponse, RegisterRequest, User,
  DashboardSummary, GaitSession, SessionDetail,
  Prediction, UploadResult, ModelPerformance, Subject,
  PaginatedResponse,
} from '../types';

import {
  MOCK_DASHBOARD, MOCK_SESSIONS, MOCK_PREDICTIONS,
  MOCK_MODEL_PERFORMANCE, MOCK_SUBJECTS, getMockSessionDetail,
} from '../data/mockData';

// ── Config ────────────────────────────────────────────────────
const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true';
const rawBaseUrl = (import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:5000').trim();
const BASE_URL  = rawBaseUrl.replace(/\/+$/, '');

const delay = (ms: number) => new Promise(res => setTimeout(res, ms));

// ── Axios instance ────────────────────────────────────────────
const http = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
});

http.interceptors.request.use(cfg => {
  const token = localStorage.getItem('gait_token');
  if (token) cfg.headers.Authorization = `Bearer ${token}`;
  return cfg;
});

http.interceptors.response.use(
  res => res,
  err => {
    const url = String(err.config?.url || '');
    const isAuthEndpoint = url.includes('/api/auth/login') || url.includes('/api/auth/register');
    const isAuthPage = typeof window !== 'undefined' && (
      window.location.pathname.startsWith('/login') || window.location.pathname.startsWith('/register')
    );

    if (err.response?.status === 401 && !isAuthEndpoint) {
      localStorage.removeItem('gait_token');
      if (!isAuthPage && typeof window !== 'undefined') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(err);
  }
);

// ── Auth ──────────────────────────────────────────────────────
export const authApi = {
  async login(data: LoginRequest): Promise<LoginResponse> {
    if (USE_MOCK) {
      await delay(600);
      if (data.email === 'demo@gaitinsight.dev' && data.password === 'demo1234') {
        const user: User = { user_id: 2, name: 'Dr. Arjun Sharma', email: data.email, role: 'researcher', created_at: '2024-01-01T00:00:00Z' };
        return { access_token: 'mock_token_demo', token_type: 'bearer', user };
      }
      throw { response: { data: { detail: 'Invalid email or password.' }, status: 401 } };
    }
    const res = await http.post<LoginResponse>('/api/auth/login', data);
    return res.data;
  },

  async register(data: RegisterRequest): Promise<User> {
    if (USE_MOCK) {
      await delay(800);
      return { user_id: 99, name: data.name, email: data.email, role: data.role, created_at: new Date().toISOString() };
    }
    const res = await http.post<User>('/api/auth/register', data);
    return res.data;
  },

  async getMe(): Promise<User> {
    if (USE_MOCK) {
      await delay(200);
      return { user_id: 2, name: 'Dr. Arjun Sharma', email: 'demo@gaitinsight.dev', role: 'researcher', created_at: '2024-01-01T00:00:00Z' };
    }
    const res = await http.get<User>('/api/users/me');
    return res.data;
  },
};

// ── Dashboard ─────────────────────────────────────────────────
export const dashboardApi = {
  async getSummary(): Promise<DashboardSummary> {
    if (USE_MOCK) { await delay(400); return MOCK_DASHBOARD; }
    const res = await http.get<DashboardSummary>('/api/dashboard/summary');
    return res.data;
  },
};

// ── Sessions ──────────────────────────────────────────────────
export const sessionsApi = {
  async getAll(params?: { page?: number; per_page?: number; gait_class?: string; search?: string }): Promise<PaginatedResponse<GaitSession>> {
    if (USE_MOCK) {
      await delay(400);
      let items = [...MOCK_SESSIONS];
      if (params?.gait_class && params.gait_class !== 'all') {
        const cls = params.gait_class;
        items = items.filter(s => MOCK_PREDICTIONS[s.session_id]?.predicted_class === cls);
      }
      if (params?.search) {
        const q = params.search.toLowerCase();
        items = items.filter(s => s.session_id.toLowerCase().includes(q) || s.subject_id.toLowerCase().includes(q));
      }
      const page = params?.page ?? 1;
      const per_page = params?.per_page ?? 5;
      const total = items.length;
      const sliced = items.slice((page - 1) * per_page, page * per_page);
      return { items: sliced, total, page, per_page, total_pages: Math.ceil(total / per_page) };
    }
    const res = await http.get<PaginatedResponse<GaitSession>>('/api/gait/sessions', { params });
    return res.data;
  },

  async getById(sessionId: string): Promise<SessionDetail> {
    if (USE_MOCK) {
      await delay(500);
      const detail = getMockSessionDetail(sessionId);
      if (!detail) throw new Error(`Session ${sessionId} not found.`);
      return detail;
    }
    const res = await http.get<SessionDetail>(`/api/gait/sessions/${sessionId}`);
    return res.data;
  },

  async delete(sessionId: string): Promise<void> {
    if (USE_MOCK) { await delay(300); return; }
    await http.delete(`/api/gait/sessions/${sessionId}`);
  },
};

// ── Upload ────────────────────────────────────────────────────
export const uploadApi = {
  async uploadCsv(file: File, onProgress?: (pct: number) => void): Promise<UploadResult> {
    if (USE_MOCK) {
      for (let p = 0; p <= 100; p += 20) {
        await delay(300);
        onProgress?.(p);
      }
      return {
        session_id: `GS-${Date.now()}`,
        rows_parsed: 3000,
        duration_seconds: 30,
        columns_found: ['timestamp','acceleration_x','acceleration_y','acceleration_z','gyroscope_x','gyroscope_y','gyroscope_z'],
        status: 'success',
        message: 'File uploaded and processed successfully.',
      };
    }
    const form = new FormData();
    form.append('file', file);
    const res = await http.post<UploadResult>('/api/gait/upload', form, {
      onUploadProgress: e => { if (e.total) onProgress?.(Math.round(e.loaded / e.total * 100)); },
    });
    return res.data;
  },
};

// ── Predictions ───────────────────────────────────────────────
export const predictionsApi = {
  async predict(sessionId: string): Promise<Prediction> {
    if (USE_MOCK) {
      await delay(800);
      const pred = MOCK_PREDICTIONS[sessionId];
      if (!pred) throw new Error('No prediction found.');
      return pred;
    }
    const res = await http.post<Prediction>(`/api/predictions/${sessionId}`);
    return res.data;
  },
};

// ── Model Performance ─────────────────────────────────────────
export const modelApi = {
  async getPerformance(): Promise<ModelPerformance> {
    if (USE_MOCK) { await delay(500); return MOCK_MODEL_PERFORMANCE; }
    const res = await http.get<ModelPerformance>('/api/model/performance');
    return res.data;
  },
};

// ── Subjects ──────────────────────────────────────────────────
export const subjectsApi = {
  async getAll(): Promise<Subject[]> {
    if (USE_MOCK) { await delay(400); return MOCK_SUBJECTS; }
    const res = await http.get<Subject[]>('/api/subjects');
    return res.data;
  },
};

export const isMockMode = USE_MOCK;
