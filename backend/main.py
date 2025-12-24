from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import json
import os

app = FastAPI(title="MY AI AGENT API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load jobs from JSON file
def load_jobs():
    paths = [
        "collected_jobs.json",
        "../collectors/collected_jobs.json",
        "collectors/collected_jobs.json"
    ]
    for path in paths:
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    data = json.load(f)
                    print(f"✅ Loaded {len(data.get('jobs', []))} jobs from {path}")
                    return data.get("jobs", [])
            except Exception as e:
                print(f"Error loading {path}: {e}")
    print("⚠️ No jobs file found, using sample data")
    return get_sample_jobs()

def get_sample_jobs():
    return [
        {
            "id": "sample-1",
            "title": "Security Engineer",
            "company": "Microsoft",
            "company_id": "microsoft",
            "industry": "Technology",
            "location": "Redmond, WA",
            "work_type": "hybrid",
            "description": "Join Microsoft's security team. H-1B sponsorship available.",
            "skills": ["Azure", "Python", "Security"],
            "categories": ["cybersecurity", "cloud"],
            "apply_url": "https://careers.microsoft.com",
            "posted_date": datetime.now().isoformat(),
            "source": "Sample",
            "opt_score": 90,
            "h1b_sponsor_history": True,
            "citizenship_required": False,
            "clearance_required": False,
            "salary_display": "$130K - $180K"
        },
        {
            "id": "sample-2",
            "title": "Cloud Security Analyst",
            "company": "Google",
            "company_id": "google",
            "industry": "Technology",
            "location": "Mountain View, CA",
            "work_type": "remote",
            "description": "Google Cloud security team. We sponsor visas.",
            "skills": ["GCP", "SIEM", "Python"],
            "categories": ["cybersecurity", "cloud"],
            "apply_url": "https://careers.google.com",
            "posted_date": datetime.now().isoformat(),
            "source": "Sample",
            "opt_score": 85,
            "h1b_sponsor_history": True,
            "citizenship_required": False,
            "clearance_required": False,
            "salary_display": "$140K - $190K"
        },
        {
            "id": "sample-3",
            "title": "Network Security Engineer",
            "company": "Palo Alto Networks",
            "company_id": "paloalto",
            "industry": "Cybersecurity",
            "location": "Santa Clara, CA",
            "work_type": "hybrid",
            "description": "Join our security team. OPT students welcome.",
            "skills": ["Firewall", "CCNA", "VPN"],
            "categories": ["cybersecurity", "networking"],
            "apply_url": "https://jobs.paloaltonetworks.com",
            "posted_date": datetime.now().isoformat(),
            "source": "Sample",
            "opt_score": 88,
            "h1b_sponsor_history": True,
            "citizenship_required": False,
            "clearance_required": False,
            "salary_display": "$120K - $160K"
        }
    ]

# Load jobs on startup
all_jobs = load_jobs()

@app.get("/")
def root():
    return {
        "name": "MY AI AGENT API",
        "version": "1.0.0",
        "jobs_count": len(all_jobs),
        "status": "running"
    }

@app.get("/api/health")
def health():
    return {
        "status": "healthy",
        "jobs_loaded": len(all_jobs),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/jobs")
def get_jobs(
    category: str = None,
    h1b_only: bool = False,
    hide_citizenship: bool = True,
    hide_clearance: bool = True,
    page: int = 1,
    page_size: int = 50
):
    filtered = all_jobs.copy()
    
    if category and category != "all":
        filtered = [j for j in filtered if category in j.get("categories", [])]
    if h1b_only:
        filtered = [j for j in filtered if j.get("h1b_sponsor_history")]
    if hide_citizenship:
        filtered = [j for j in filtered if not j.get("citizenship_required")]
    if hide_clearance:
        filtered = [j for j in filtered if not j.get("clearance_required")]
    
    total = len(filtered)
    start = (page - 1) * page_size
    end = start + page_size
    
    return {
        "jobs": filtered[start:end],
        "total": total,
        "page": page,
        "page_size": page_size
    }

@app.get("/api/stats")
def get_stats():
    return {
        "total_jobs": len(all_jobs),
        "total_companies": len(set(j.get("company") for j in all_jobs)),
        "h1b_sponsors": len(set(j.get("company") for j in all_jobs if j.get("h1b_sponsor_history"))),
        "by_category": {
            "cybersecurity": len([j for j in all_jobs if "cybersecurity" in j.get("categories", [])]),
            "cloud": len([j for j in all_jobs if "cloud" in j.get("categories", [])]),
            "networking": len([j for j in all_jobs if "networking" in j.get("categories", [])]),
            "business_analyst": len([j for j in all_jobs if "business_analyst" in j.get("categories", [])])
        }
    }

@app.get("/api/companies")
def get_companies():
    companies = {}
    for job in all_jobs:
        cid = job.get("company_id", "")
        if cid and cid not in companies:
            companies[cid] = {
                "id": cid,
                "name": job.get("company"),
                "h1b_sponsor": job.get("h1b_sponsor_history"),
                "job_count": 0
            }
        if cid:
            companies[cid]["job_count"] += 1
    return {"companies": list(companies.values()), "total": len(companies)}
```

### Step 3: Commit the changes

1. Scroll down
2. Click **"Commit changes"**
3. Click **"Commit changes"** again

---

## Step 4: Wait for Render to redeploy

Render will automatically detect the change and redeploy (takes 2-3 minutes).

Then test again:
```
https://my-ai-agent-5eos.onrender.com/api/health
