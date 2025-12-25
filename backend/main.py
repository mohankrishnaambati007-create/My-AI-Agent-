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
        "../collectors/collected_jobs.json",
        "collectors/collected_jobs.json", 
        "collected_jobs.json"
    ]
    for path in paths:
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    data = json.load(f)
                    jobs = data.get("jobs", [])
                    print(f"SUCCESS: Loaded {len(jobs)} jobs from {path}")
                    return jobs
            except Exception as e:
                print(f"Error: {e}")
    print("No jobs file found")
    return []

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
    cats = {}
    for j in all_jobs:
        for c in j.get("categories", []):
            cats[c] = cats.get(c, 0) + 1
    return {
        "total_jobs": len(all_jobs),
        "total_companies": len(set(j.get("company") for j in all_jobs)),
        "h1b_sponsors": len(set(j.get("company") for j in all_jobs if j.get("h1b_sponsor_history"))),
        "by_category": cats
    }

@app.get("/api/companies")
def get_companies():
    return {"companies": [], "total": len(set(j.get("company") for j in all_jobs))}
```

5. Click **"Commit changes"**

---

### Step 2: Wait for Render to Redeploy

Render will automatically detect the change and redeploy (2-3 minutes).

Or go to [render.com](https://render.com) → Your service → **"Manual Deploy"** → **"Deploy latest commit"**

---

### Step 3: Check Render Logs

After deployment, check the Render logs. You should see:
```
SUCCESS: Loaded 4177 jobs from ../collectors/collected_jobs.json
