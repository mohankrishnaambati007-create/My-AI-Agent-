"""
MY AI AGENT - Production Backend API
Deployment-ready for Render/Railway (FREE tier)
With Supabase database support
"""

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
import json
import os
import httpx
import asyncio
import re

# ==================== CONFIGURATION ====================

# Environment variables for production
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")  # For email notifications

# ==================== DATABASE CLIENT ====================

class DatabaseClient:
    """Simple database client - works with Supabase or local JSON"""
    
    def __init__(self):
        self.jobs = []
        self.use_supabase = bool(SUPABASE_URL and SUPABASE_KEY)
        
    async def init(self):
        """Initialize database connection"""
        if self.use_supabase:
            await self.load_from_supabase()
        else:
            self.load_from_json()
    
    def load_from_json(self):
        """Load from local JSON file"""
        paths = ["collected_jobs.json", "collectors/collected_jobs.json", "../collectors/collected_jobs.json"]
        for path in paths:
            if os.path.exists(path):
                try:
                    with open(path, "r") as f:
                        data = json.load(f)
                        self.jobs = data.get("jobs", [])
                        print(f"✅ Loaded {len(self.jobs)} jobs from {path}")
                        return
                except Exception as e:
                    print(f"Error loading {path}: {e}")
        print("⚠️ No job data found, starting empty")
        self.jobs = []
    
    async def load_from_supabase(self):
        """Load jobs from Supabase"""
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{SUPABASE_URL}/rest/v1/jobs?select=*&order=posted_date.desc&limit=5000",
                    headers={
                        "apikey": SUPABASE_KEY,
                        "Authorization": f"Bearer {SUPABASE_KEY}"
                    }
                )
                if resp.status_code == 200:
                    self.jobs = resp.json()
                    print(f"✅ Loaded {len(self.jobs)} jobs from Supabase")
                else:
                    print(f"Supabase error: {resp.status_code}")
                    self.load_from_json()
        except Exception as e:
            print(f"Supabase connection failed: {e}")
            self.load_from_json()
    
    async def save_jobs(self, jobs: List[Dict]):
        """Save jobs to database"""
        if self.use_supabase:
            await self.save_to_supabase(jobs)
        else:
            self.save_to_json(jobs)
        self.jobs = jobs
    
    def save_to_json(self, jobs: List[Dict]):
        """Save to local JSON"""
        with open("collected_jobs.json", "w") as f:
            json.dump({"jobs": jobs, "updated_at": datetime.now().isoformat()}, f)
    
    async def save_to_supabase(self, jobs: List[Dict]):
        """Save to Supabase (upsert)"""
        try:
            async with httpx.AsyncClient() as client:
                # Batch insert in chunks of 100
                for i in range(0, len(jobs), 100):
                    batch = jobs[i:i+100]
                    await client.post(
                        f"{SUPABASE_URL}/rest/v1/jobs",
                        headers={
                            "apikey": SUPABASE_KEY,
                            "Authorization": f"Bearer {SUPABASE_KEY}",
                            "Content-Type": "application/json",
                            "Prefer": "resolution=merge-duplicates"
                        },
                        json=batch
                    )
        except Exception as e:
            print(f"Supabase save error: {e}")

db = DatabaseClient()

# ==================== LIFESPAN ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    await db.init()
    yield
    print("Shutting down...")

# ==================== APP ====================

app = FastAPI(
    title="MY AI AGENT API",
    description="Job Discovery Platform for F-1 OPT Students",
    version="3.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, set specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== MODELS ====================

class EmailSubscription(BaseModel):
    email: str
    keywords: List[str] = ["security", "cloud", "analyst"]
    min_opt_score: int = 70
    locations: List[str] = []

class JobSearchRequest(BaseModel):
    query: Optional[str] = None
    category: Optional[str] = None
    hours_ago: Optional[int] = None
    work_type: Optional[str] = None
    h1b_only: bool = False
    hide_citizenship: bool = True
    hide_clearance: bool = True
    min_opt_score: int = 0
    page: int = 1
    page_size: int = 50

# ==================== JOB SEARCH ====================

def search_jobs(params: JobSearchRequest) -> Dict:
    """Search and filter jobs"""
    results = db.jobs.copy()
    
    # Time filter
    if params.hours_ago and params.hours_ago > 0:
        cutoff = datetime.now() - timedelta(hours=params.hours_ago)
        results = [j for j in results if datetime.fromisoformat(j.get("posted_date", "2020-01-01").replace("Z", "")) >= cutoff]
    
    # Work type filter
    if params.work_type and params.work_type != "all":
        results = [j for j in results if j.get("work_type", "").lower() == params.work_type.lower()]
    
    # Category filter
    if params.category and params.category != "all":
        results = [j for j in results if params.category in j.get("categories", [])]
    
    # Visa filters
    if params.h1b_only:
        results = [j for j in results if j.get("h1b_sponsor_history")]
    if params.hide_citizenship:
        results = [j for j in results if not j.get("citizenship_required")]
    if params.hide_clearance:
        results = [j for j in results if not j.get("clearance_required")]
    
    # OPT score filter
    if params.min_opt_score > 0:
        results = [j for j in results if j.get("opt_score", 0) >= params.min_opt_score]
    
    # Text search
    if params.query:
        q = params.query.lower()
        results = [j for j in results if 
            q in j.get("title", "").lower() or
            q in j.get("company", "").lower() or
            q in j.get("description", "").lower() or
            any(q in s.lower() for s in j.get("skills", []))]
    
    # Sort by OPT score and recency
    results.sort(key=lambda x: (x.get("opt_score", 0), x.get("posted_date", "")), reverse=True)
    
    # Paginate
    total = len(results)
    start = (params.page - 1) * params.page_size
    end = start + params.page_size
    
    return {
        "jobs": results[start:end],
        "total": total,
        "page": params.page,
        "page_size": params.page_size
    }

# ==================== ENDPOINTS ====================

@app.get("/")
async def root():
    """API info"""
    return {
        "name": "MY AI AGENT API",
        "version": "3.0.0",
        "jobs_count": len(db.jobs),
        "database": "supabase" if db.use_supabase else "local",
        "docs": "/docs"
    }

@app.get("/api/jobs")
async def get_jobs(
    query: Optional[str] = None,
    category: Optional[str] = None,
    hours_ago: Optional[int] = None,
    work_type: Optional[str] = None,
    h1b_only: bool = False,
    hide_citizenship: bool = True,
    hide_clearance: bool = True,
    min_opt_score: int = 0,
    page: int = 1,
    page_size: int = 50
):
    """Get filtered jobs"""
    params = JobSearchRequest(
        query=query, category=category, hours_ago=hours_ago,
        work_type=work_type, h1b_only=h1b_only,
        hide_citizenship=hide_citizenship, hide_clearance=hide_clearance,
        min_opt_score=min_opt_score, page=page, page_size=page_size
    )
    return search_jobs(params)

@app.post("/api/jobs/search")
async def search_jobs_post(params: JobSearchRequest):
    """Advanced job search"""
    return search_jobs(params)

@app.get("/api/jobs/{job_id}")
async def get_job(job_id: str):
    """Get single job by ID"""
    for job in db.jobs:
        if job.get("id") == job_id:
            return job
    raise HTTPException(status_code=404, detail="Job not found")

@app.get("/api/stats")
async def get_stats():
    """Get statistics"""
    jobs = db.jobs
    now = datetime.now()
    
    return {
        "total_jobs": len(jobs),
        "total_companies": len(set(j.get("company") for j in jobs)),
        "h1b_sponsors": len(set(j.get("company") for j in jobs if j.get("h1b_sponsor_history"))),
        "opt_friendly": len([j for j in jobs if j.get("opt_score", 0) >= 70]),
        "jobs_24h": len([j for j in jobs if (now - datetime.fromisoformat(j.get("posted_date", "2020-01-01").replace("Z", ""))).total_seconds() < 86400]),
        "jobs_7d": len([j for j in jobs if (now - datetime.fromisoformat(j.get("posted_date", "2020-01-01").replace("Z", ""))).total_seconds() < 604800]),
        "by_category": {
            "cybersecurity": len([j for j in jobs if "cybersecurity" in j.get("categories", [])]),
            "cloud": len([j for j in jobs if "cloud" in j.get("categories", [])]),
            "networking": len([j for j in jobs if "networking" in j.get("categories", [])]),
            "business_analyst": len([j for j in jobs if "business_analyst" in j.get("categories", [])])
        },
        "last_updated": max((j.get("posted_date", "") for j in jobs), default="N/A")
    }

@app.get("/api/companies")
async def get_companies():
    """Get all companies with job counts"""
    companies = {}
    for job in db.jobs:
        cid = job.get("company_id", job.get("company", "").lower().replace(" ", "-"))
        if cid not in companies:
            companies[cid] = {
                "id": cid,
                "name": job.get("company"),
                "industry": job.get("industry"),
                "h1b_sponsor": job.get("h1b_sponsor_history"),
                "job_count": 0
            }
        companies[cid]["job_count"] += 1
    
    return {
        "companies": sorted(companies.values(), key=lambda x: -x["job_count"]),
        "total": len(companies)
    }

@app.get("/api/health")
async def health():
    """Health check for deployment platforms"""
    return {
        "status": "healthy",
        "jobs_loaded": len(db.jobs),
        "database": "supabase" if db.use_supabase else "local",
        "timestamp": datetime.now().isoformat()
    }

# ==================== EMAIL NOTIFICATIONS ====================

email_subscribers = []  # In production, store in database

@app.post("/api/subscribe")
async def subscribe_email(subscription: EmailSubscription):
    """Subscribe to job alerts"""
    email_subscribers.append(subscription.dict())
    return {"status": "subscribed", "email": subscription.email}

@app.delete("/api/unsubscribe/{email}")
async def unsubscribe_email(email: str):
    """Unsubscribe from alerts"""
    global email_subscribers
    email_subscribers = [s for s in email_subscribers if s["email"] != email]
    return {"status": "unsubscribed"}

async def send_email_notification(to_email: str, subject: str, html_content: str):
    """Send email via Resend API (FREE tier: 100 emails/day)"""
    if not RESEND_API_KEY:
        print("Email not configured - RESEND_API_KEY not set")
        return False
    
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {RESEND_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "from": "MY AI AGENT <jobs@myaiagent.com>",
                    "to": [to_email],
                    "subject": subject,
                    "html": html_content
                }
            )
            return resp.status_code == 200
    except Exception as e:
        print(f"Email error: {e}")
        return False

# ==================== JOB COLLECTOR (runs on schedule) ====================

@app.post("/api/collect")
async def trigger_collection(background_tasks: BackgroundTasks):
    """Manually trigger job collection"""
    background_tasks.add_task(run_collector)
    return {"status": "collection_started"}

async def run_collector():
    """Run job collection from APIs"""
    from collectors.live_collector import collect_all_jobs
    result = await collect_all_jobs()
    await db.save_jobs(result.get("jobs", []))
    
    # Send notifications to subscribers
    new_jobs = result.get("jobs", [])[:10]
    for sub in email_subscribers:
        matching = [j for j in new_jobs if j.get("opt_score", 0) >= sub.get("min_opt_score", 0)]
        if matching:
            await send_job_alert_email(sub["email"], matching)

async def send_job_alert_email(email: str, jobs: List[Dict]):
    """Send job alert email"""
    jobs_html = "".join([
        f"""<div style="padding:15px;border:1px solid #ddd;margin:10px 0;border-radius:8px;">
            <h3 style="margin:0;color:#00f5d4;">{j['title']}</h3>
            <p style="margin:5px 0;color:#666;">{j['company']} • {j['location']}</p>
            <p style="margin:5px 0;">OPT Score: <strong>{j['opt_score']}</strong></p>
            <a href="{j['apply_url']}" style="color:#00bbf9;">Apply Now →</a>
        </div>"""
        for j in jobs[:5]
    ])
    
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
        <h1 style="color:#00f5d4;">🚀 New OPT-Friendly Jobs!</h1>
        <p>We found {len(jobs)} new positions matching your criteria:</p>
        {jobs_html}
        <p style="margin-top:20px;color:#666;">
            <a href="https://myaiagent.vercel.app">View all jobs →</a>
        </p>
    </div>
    """
    
    await send_email_notification(email, f"🚀 {len(jobs)} New Jobs for You!", html)

# ==================== MAIN ====================

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
