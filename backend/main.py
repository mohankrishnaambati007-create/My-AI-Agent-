from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import json
import os

app = FastAPI(title="MY AI AGENT API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
                    jobs = data.get("jobs", [])
                    print(f"Loaded {len(jobs)} jobs from {path}")
                    return jobs
            except:
                pass
    return get_sample_jobs()

def get_sample_jobs():
    return [
        {"id": "1", "title": "Security Engineer", "company": "Microsoft", "company_id": "microsoft", "industry": "Technology", "location": "Redmond, WA", "work_type": "hybrid", "skills": ["Azure", "Python"], "categories": ["cybersecurity", "cloud"], "apply_url": "https://careers.microsoft.com", "posted_date": "2024-12-24T10:00:00", "opt_score": 90, "h1b_sponsor_history": True, "citizenship_required": False, "clearance_required": False, "salary_display": "$130K-$180K"},
        {"id": "2", "title": "Cloud Security Analyst", "company": "Google", "company_id": "google", "industry": "Technology", "location": "Mountain View, CA", "work_type": "remote", "skills": ["GCP", "SIEM"], "categories": ["cybersecurity", "cloud"], "apply_url": "https://careers.google.com", "posted_date": "2024-12-24T09:00:00", "opt_score": 85, "h1b_sponsor_history": True, "citizenship_required": False, "clearance_required": False, "salary_display": "$140K-$190K"},
        {"id": "3", "title": "Network Engineer", "company": "Cisco", "company_id": "cisco", "industry": "Networking", "location": "San Jose, CA", "work_type": "hybrid", "skills": ["CCNA", "Firewall"], "categories": ["networking"], "apply_url": "https://jobs.cisco.com", "posted_date": "2024-12-24T08:00:00", "opt_score": 80, "h1b_sponsor_history": True, "citizenship_required": False, "clearance_required": False, "salary_display": "$110K-$150K"}
    ]

all_jobs = load_jobs()

@app.get("/")
def root():
    return {"name": "MY AI AGENT API", "jobs": len(all_jobs)}

@app.get("/api/health")
def health():
    return {"status": "healthy", "jobs_loaded": len(all_jobs)}

@app.get("/api/jobs")
def get_jobs(page: int = 1, page_size: int = 500):
    return {"jobs": all_jobs, "total": len(all_jobs), "page": page}

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
    return {"companies": [], "total": len(set(j.get("company") for j in all_jobs))}
