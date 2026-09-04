# Deployment Guide: Render (Backend) & Vercel (Frontend)

This guide walks through deploying the **Gait Abnormality Classification & GaitInsight** project to **Render** (Flask API) and **Vercel** (React Frontend).

---

## 🚀 Part 1: Deploy Backend to Render

### Option A: Render Blueprint (Easiest)
1. Push your repository to GitHub.
2. Go to [dashboard.render.com](https://dashboard.render.com/) -> **New** -> **Blueprint**.
3. Connect your GitHub repository.
4. Render will read `render.yaml` automatically and configure the service.

### Option B: Manual Web Service Setup on Render
1. Go to [dashboard.render.com](https://dashboard.render.com/) -> **New** -> **Web Service**.
2. Connect your repository.
3. Configure the following settings:
   - **Name**: `gait-abnormality-api` (or your choice)
   - **Root Directory**: `gait-abnormality-system`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn -w 2 -b 0.0.0.0:$PORT "app.app:app"`
   - **Health Check Path**: `/api/health`
4. Under **Environment Variables**, add:
   - `PYTHON_VERSION`: `3.11.9` (or `3.12.x`)
   - `SECRET_KEY`: *[Click Generate or type a secure random string]*
   - `MODEL_PATH`: `models/gait_model_v1.pkl`
   - `CORS_ORIGINS`: `*` (or your Vercel URL once deployed)
   - *(Optional PostgreSQL)*: `DATABASE_URL`: *[Your Render/Neon/Supabase PostgreSQL connection string if using PostgreSQL]*
5. Click **Deploy Web Service**.
6. Copy your public Render URL once deployed (e.g., `https://gait-abnormality-api.onrender.com`).

---

## 🌐 Part 2: Deploy Frontend to Vercel

1. Go to [vercel.com](https://vercel.com/) -> **Add New** -> **Project**.
2. Import your GitHub repository.
3. In **Project Settings**:
   - **Framework Preset**: `Vite`
   - **Root Directory**: Click `Edit` and select `gait-insight-frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
   - **Install Command**: `npm install`
4. Under **Environment Variables**, add:
   - `VITE_USE_MOCK`: `false`
   - `VITE_API_BASE_URL`: `https://your-render-backend-url.onrender.com` *(Replace with your Render API URL from Part 1, without trailing slash)*
   - `VITE_APP_NAME`: `GaitInsight`
   - `VITE_APP_VERSION`: `1.0.0`
5. Click **Deploy**.

---

## 🔐 Sign-In and Registration Verification

Once deployed:
1. **Demo Account**:
   - Email: `demo@gaitinsight.dev`
   - Password: `demo1234`
2. **New Account Registration**:
   - Go to `https://your-app.vercel.app/register`
   - Fill in Full Name, Email, Role, and Password (min 8 chars)
   - Check the research disclaimer and click **Create Account**
   - You will be redirected to the sign-in page to log in with your newly created credentials.
3. **Render Cold Start Note**:
   - On Render's free tier, the web service automatically spins down after 15 minutes of inactivity.
   - The first request after sleep may take ~30–50 seconds to respond. The UI displays helpful guidance if the server is still waking up.
