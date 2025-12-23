# 🚀 MY AI AGENT - FREE Deployment Guide

Deploy your job discovery platform for **FREE** using Vercel + Render!

## 📋 What You'll Get

| Component | Service | Cost | URL |
|-----------|---------|------|-----|
| Frontend | Vercel | FREE | `your-app.vercel.app` |
| Backend API | Render | FREE | `your-api.onrender.com` |
| Database | Supabase | FREE | 50,000 rows |
| Auto-Collection | GitHub Actions | FREE | Daily job refresh |
| Email Alerts | Resend | FREE | 100 emails/day |

---

## 🔧 Step-by-Step Deployment

### Step 1: Create GitHub Repository

1. Go to [github.com](https://github.com) and create a new repository
2. Name it `my-ai-agent`
3. Make it **Public** (required for free tier)
4. Upload all files from this folder

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/my-ai-agent.git
git push -u origin main
```

---

### Step 2: Deploy Frontend to Vercel (FREE)

1. Go to [vercel.com](https://vercel.com) and sign up with GitHub
2. Click **"New Project"**
3. Import your `my-ai-agent` repository
4. Set **Root Directory** to `frontend`
5. Click **Deploy**

✅ Your frontend will be live at: `https://my-ai-agent.vercel.app`

---

### Step 3: Deploy Backend to Render (FREE)

1. Go to [render.com](https://render.com) and sign up with GitHub
2. Click **"New" → "Web Service"**
3. Connect your `my-ai-agent` repository
4. Configure:
   - **Name**: `my-ai-agent-api`
   - **Root Directory**: `backend`
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Select **Free** plan
6. Click **Create Web Service**

✅ Your API will be live at: `https://my-ai-agent-api.onrender.com`

**⚠️ IMPORTANT**: Update `API_BASE` in `frontend/index.html` with your Render URL!

---

### Step 4: Set Up Database (Supabase - FREE)

1. Go to [supabase.com](https://supabase.com) and create account
2. Create new project
3. Go to **SQL Editor** and run:

```sql
CREATE TABLE jobs (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    company TEXT NOT NULL,
    company_id TEXT,
    industry TEXT,
    location TEXT,
    work_type TEXT,
    description TEXT,
    skills TEXT[],
    categories TEXT[],
    apply_url TEXT,
    posted_date TIMESTAMP,
    source TEXT,
    opt_score INTEGER DEFAULT 50,
    h1b_sponsor_history BOOLEAN DEFAULT false,
    citizenship_required BOOLEAN DEFAULT false,
    clearance_required BOOLEAN DEFAULT false,
    salary_display TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_jobs_posted ON jobs(posted_date DESC);
CREATE INDEX idx_jobs_opt_score ON jobs(opt_score DESC);
CREATE INDEX idx_jobs_company ON jobs(company);
```

4. Go to **Settings → API** and copy:
   - `URL` (Project URL)
   - `anon public` key

5. Add to Render environment variables:
   - `SUPABASE_URL`: your project URL
   - `SUPABASE_KEY`: your anon key

---

### Step 5: Set Up Daily Job Collection (GitHub Actions - FREE)

1. In your GitHub repo, go to **Settings → Secrets → Actions**
2. Add these secrets:
   - `SUPABASE_URL`: your Supabase URL
   - `SUPABASE_KEY`: your Supabase anon key
   - `API_URL`: your Render API URL

3. The workflow in `.github/workflows/collect-jobs.yml` will run daily at 6 AM UTC

4. To run manually: Go to **Actions → Daily Job Collection → Run workflow**

---

### Step 6: Set Up Email Notifications (Resend - FREE)

1. Go to [resend.com](https://resend.com) and create account
2. Get your API key
3. Add to Render environment variables:
   - `RESEND_API_KEY`: your Resend API key

4. You'll need to verify a domain or use Resend's test domain

---

## 🎯 Environment Variables Summary

### Render (Backend)
```
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIs...
OPENAI_API_KEY=sk-...  (optional, for AI features)
RESEND_API_KEY=re_...  (optional, for email alerts)
```

### GitHub Secrets (for Actions)
```
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIs...
API_URL=https://my-ai-agent-api.onrender.com
```

---

## 🔄 How It Works

```
┌─────────────────────────────────────────────────────────┐
│  GitHub Actions (Daily at 6 AM UTC)                     │
│  └─> Runs live_collector.py                             │
│      └─> Fetches jobs from Greenhouse/Lever APIs        │
│          └─> Saves to Supabase database                 │
├─────────────────────────────────────────────────────────┤
│  Render Backend (Always running)                        │
│  └─> Serves API at /api/jobs, /api/stats, etc.          │
│      └─> Reads from Supabase                            │
│          └─> Sends email alerts (optional)              │
├─────────────────────────────────────────────────────────┤
│  Vercel Frontend (Static hosting)                       │
│  └─> Calls Render API                                   │
│      └─> Displays jobs with filters                     │
│          └─> Users can search, filter, apply            │
└─────────────────────────────────────────────────────────┘
```

---

## 🆘 Troubleshooting

### "API not connecting"
- Check if Render service is running (may sleep after 15 min of inactivity on free tier)
- Verify `API_BASE` URL in frontend/index.html

### "No jobs showing"
- Run GitHub Action manually to collect jobs
- Check Supabase table for data

### "Email not sending"
- Verify Resend API key
- Check Resend dashboard for errors

---

## 💰 Cost Breakdown

| Service | Free Tier Limits | Your Usage |
|---------|------------------|------------|
| Vercel | 100GB bandwidth/month | ~1GB |
| Render | 750 hours/month | ~720 hours |
| Supabase | 500MB database | ~50MB |
| GitHub Actions | 2000 min/month | ~30 min |
| Resend | 100 emails/day | ~10-50 |

**Total Cost: $0/month** ✅

---

## 📞 Support

Created by MY AI AGENT
For F-1 OPT students seeking employment in the USA 🇺🇸

Good luck with your job search! 🍀
