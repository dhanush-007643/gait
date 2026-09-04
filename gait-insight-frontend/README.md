# GaitInsight Frontend

**Wearable Sensor-Based Real-Time Monitoring and Classification of Human Gait Abnormalities**

B.Tech Biotechnology Capstone Project — Human Anatomy and Physiology

---

## Tech Stack

| Tool | Version | Purpose |
|------|---------|---------|
| React | 18 | UI framework |
| TypeScript | 5 | Type safety |
| Vite | 5 | Build tool |
| Tailwind CSS | 3 | Styling |
| React Router | 6 | Client routing |
| Recharts | 2 | Charts |
| Lucide React | latest | Icons |
| Axios | latest | HTTP client |

---

## Prerequisites

**Node.js is required.** Download from https://nodejs.org (LTS version, v18 or higher).

Verify installation:
```powershell
node --version   # v18+
npm --version    # v9+
```

---

## Quick Start

```powershell
# 1. Navigate into the project
cd gait-insight-frontend

# 2. Copy the environment file
copy .env.example .env

# 3. Install dependencies
npm install

# 4. Start the dev server
npm run dev

# → App runs at http://localhost:3000
```

---

## Demo Mode (Default)

By default, `VITE_USE_MOCK=true` in `.env`. This means:

- All data is **synthetic** (computer-generated)
- No backend server required
- A **"Demo Mode — Using Synthetic Data"** banner is always shown
- Demo login: `demo@gaitinsight.dev` / `demo1234`

**To connect to the real Flask backend:**
```env
VITE_USE_MOCK=false
VITE_API_BASE_URL=http://localhost:5000
```

---

## Project Structure

```
src/
├── components/
│   ├── layout/
│   │   ├── Sidebar.tsx      ← Nav, mobile hamburger, user panel
│   │   ├── Header.tsx       ← Title, demo badge, user dropdown
│   │   └── Layout.tsx       ← Sidebar + Header wrapper
│   └── ui/
│       ├── StatCard.tsx
│       ├── ChartCard.tsx
│       ├── GaitBadge.tsx    ← Color-coded per gait class
│       ├── SensorChart.tsx  ← Recharts line chart
│       ├── LoadingState.tsx ← Skeleton + spinner
│       ├── EmptyState.tsx
│       ├── ErrorState.tsx
│       ├── Modal.tsx
│       ├── ConfirmationDialog.tsx
│       └── Pagination.tsx
├── pages/
│   ├── Login.tsx
│   ├── Register.tsx
│   ├── Dashboard.tsx        ← Stat cards + donut chart + sensor chart
│   ├── UploadData.tsx       ← Drag-drop + progress steps
│   ├── LiveMonitoring.tsx   ← Simulated real-time sensor stream
│   ├── Analysis.tsx         ← Prediction + parameter table + charts
│   ├── Sessions.tsx         ← Table with search/filter/pagination
│   ├── SessionDetail.tsx
│   ├── Reports.tsx          ← Print-ready report preview
│   ├── Subjects.tsx
│   ├── ModelPerformance.tsx ← Accuracy/F1 cards + confusion matrix
│   ├── Settings.tsx
│   └── HelpSupport.tsx      ← FAQ accordion + workflow diagram
├── services/
│   └── api.ts               ← All API calls (mock/real switch)
├── types/
│   └── index.ts             ← All TypeScript interfaces
├── data/
│   └── mockData.ts          ← SYNTHETIC demo data (labeled)
├── context/
│   └── AuthContext.tsx
├── App.tsx                  ← Router + ProtectedRoute
└── main.tsx
```

---

## Pages Reference

| Page | Route | Description |
|------|-------|-------------|
| Login | `/login` | Auth with demo mode pre-fill |
| Register | `/register` | Password strength + role select |
| Dashboard | `/` | Summary stats, donut chart, gait params |
| Upload Data | `/upload` | CSV drag-drop + animated progress |
| Live Monitoring | `/monitoring` | Simulated sensor stream + controls |
| Analysis | `/analysis/:id` | Prediction, probability chart, radar |
| Sessions | `/sessions` | Table with search/filter/pagination |
| Session Detail | `/sessions/:id` | Full session + charts |
| Reports | `/reports/:id` | Print-ready report + download |
| Subjects | `/subjects` | Subject IDs only (no PII) |
| Model Performance | `/model` | Accuracy, F1, confusion matrix |
| Settings | `/settings` | Profile, preferences, security |
| Help & Support | `/help` | FAQ accordion + workflow |

---

## Gait Classes

| Class | Color | Description |
|-------|-------|-------------|
| Normal | 🟢 Green | Healthy adult walking |
| Parkinsonian | 🟠 Orange | Shuffling, festination |
| Hemiplegic | 🔴 Red | Unilateral weakness |
| Ataxic | 🟣 Purple | Wide-based, staggering |
| Spastic | 🩵 Cyan | Scissor gait |
| Antalgic | 🟡 Yellow | Pain-avoidance gait |

---

## Backend Integration

The frontend expects these API endpoints (from the Flask/FastAPI backend):

```
POST /api/auth/login
POST /api/auth/register
GET  /api/users/me
GET  /api/dashboard/summary
GET  /api/gait/sessions
GET  /api/gait/sessions/{id}
DELETE /api/gait/sessions/{id}
POST /api/gait/upload
POST /api/predictions/{id}
GET  /api/model/performance
GET  /api/reports/{id}
GET  /api/subjects
```

All requests include `Authorization: Bearer <token>` header automatically.

---

## Build for Production

```powershell
npm run build
# Output in dist/
```

---

## Disclaimer

> This application is a research/educational prototype for gait pattern analysis.
> It is **not a medical diagnostic device** and should not replace assessment by a qualified healthcare professional.
> Outputs are for research and educational purposes only.

---

*Course: Human Anatomy and Physiology | B.Tech Biotechnology | Capstone Project*
