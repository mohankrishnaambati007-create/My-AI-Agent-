"""
MY AI AGENT - Live Job Collector
Fetches REAL jobs from Greenhouse and Lever APIs
"""

import asyncio
import httpx
import json
import re
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path

# ==================== CONFIGURATION ====================

# Keywords to filter relevant jobs
TARGET_KEYWORDS = [
    # Cybersecurity
    "security", "cyber", "soc", "analyst", "incident", "threat", "vulnerability",
    "penetration", "compliance", "grc", "risk", "iam", "identity",
    # Cloud
    "cloud", "aws", "azure", "gcp", "devops", "sre", "infrastructure", "platform",
    "kubernetes", "docker",
    # Networking  
    "network", "cisco", "firewall", "vpn",
    # Business Analyst
    "business analyst", "data analyst", "product", "analytics", "bi ",
    # AI/ML
    "machine learning", "ml ", "ai ", "data scientist"
]

# ==================== GREENHOUSE COMPANIES ====================

GREENHOUSE_COMPANIES = {
    "airbnb": {"name": "Airbnb", "h1b": True, "lca": 287, "industry": "Technology"},
    "stripe": {"name": "Stripe", "h1b": True, "lca": 432, "industry": "Fintech"},
    "databricks": {"name": "Databricks", "h1b": True, "lca": 654, "industry": "Technology"},
    "cloudflare": {"name": "Cloudflare", "h1b": True, "lca": 287, "industry": "Technology"},
    "doordash": {"name": "DoorDash", "h1b": True, "lca": 321, "industry": "Technology"},
    "lyft": {"name": "Lyft", "h1b": True, "lca": 234, "industry": "Technology"},
    "twilio": {"name": "Twilio", "h1b": True, "lca": 321, "industry": "Technology"},
    "zscaler": {"name": "Zscaler", "h1b": True, "lca": 345, "industry": "Cybersecurity"},
    "paloaltonetworks": {"name": "Palo Alto Networks", "h1b": True, "lca": 789, "industry": "Cybersecurity"},
    "okta": {"name": "Okta", "h1b": True, "lca": 432, "industry": "Cybersecurity"},
    "figma": {"name": "Figma", "h1b": True, "lca": 156, "industry": "Technology"},
    "notion": {"name": "Notion", "h1b": True, "lca": 123, "industry": "Technology"},
    "discord": {"name": "Discord", "h1b": True, "lca": 189, "industry": "Technology"},
    "ramp": {"name": "Ramp", "h1b": True, "lca": 145, "industry": "Fintech"},
    "brex": {"name": "Brex", "h1b": True, "lca": 167, "industry": "Fintech"},
    "airtable": {"name": "Airtable", "h1b": True, "lca": 134, "industry": "Technology"},
    "flexport": {"name": "Flexport", "h1b": True, "lca": 212, "industry": "Logistics"},
    "gusto": {"name": "Gusto", "h1b": True, "lca": 178, "industry": "Technology"},
    "plaid": {"name": "Plaid", "h1b": True, "lca": 198, "industry": "Fintech"},
    "asana": {"name": "Asana", "h1b": True, "lca": 145, "industry": "Technology"},
    "gitlab": {"name": "GitLab", "h1b": True, "lca": 234, "industry": "Technology"},
    "hashicorp": {"name": "HashiCorp", "h1b": True, "lca": 187, "industry": "Technology"},
    "datadog": {"name": "Datadog", "h1b": True, "lca": 321, "industry": "Technology"},
    "mongodb": {"name": "MongoDB", "h1b": True, "lca": 234, "industry": "Technology"},
    "elastic": {"name": "Elastic", "h1b": True, "lca": 198, "industry": "Technology"},
    "confluent": {"name": "Confluent", "h1b": True, "lca": 167, "industry": "Technology"},
    "cockroachlabs": {"name": "Cockroach Labs", "h1b": True, "lca": 98, "industry": "Technology"},
    "snyk": {"name": "Snyk", "h1b": True, "lca": 145, "industry": "Cybersecurity"},
    "lacework": {"name": "Lacework", "h1b": True, "lca": 87, "industry": "Cybersecurity"},
    "sentinelone": {"name": "SentinelOne", "h1b": True, "lca": 234, "industry": "Cybersecurity"},
}

# ==================== LEVER COMPANIES ====================

LEVER_COMPANIES = {
    "netflix": {"name": "Netflix", "h1b": True, "lca": 432, "industry": "Technology"},
    "shopify": {"name": "Shopify", "h1b": True, "lca": 567, "industry": "E-commerce"},
    "coinbase": {"name": "Coinbase", "h1b": True, "lca": 298, "industry": "Fintech"},
    "robinhood": {"name": "Robinhood", "h1b": True, "lca": 234, "industry": "Fintech"},
    "reddit": {"name": "Reddit", "h1b": True, "lca": 189, "industry": "Technology"},
    "webflow": {"name": "Webflow", "h1b": True, "lca": 98, "industry": "Technology"},
    "vercel": {"name": "Vercel", "h1b": True, "lca": 76, "industry": "Technology"},
    "linear": {"name": "Linear", "h1b": True, "lca": 45, "industry": "Technology"},
    "retool": {"name": "Retool", "h1b": True, "lca": 87, "industry": "Technology"},
    "loom": {"name": "Loom", "h1b": True, "lca": 67, "industry": "Technology"},
}

# ==================== VISA ANALYZER ====================

CITIZENSHIP_PATTERNS = [
    r'\b(us|u\.s\.|united states)\s*(citizen|citizenship)\s*(required|only|must)\b',
    r'\bmust be\s*(a\s*)?(us|u\.s\.)\s*citizen\b',
    r'\bno\s*(visa\s*)?sponsorship\b',
    r'\bwithout\s*(need for\s*)?sponsorship\b',
    r'\bauthorized to work.*without.*sponsor\b',
    r'\bpermanent.*authorization\s*required\b',
    r'\bgreen card.*required\b',
]

CLEARANCE_PATTERNS = [
    r'\b(security\s*)?clearance\s*(required|needed|must)\b',
    r'\b(ts|top secret|secret|sci)\s*(clearance)?\s*(required|eligible)\b',
    r'\bmust.*obtain.*clearance\b',
    r'\bactive.*clearance\b',
]

H1B_POSITIVE_PATTERNS = [
    r'\b(h-?1b|visa)\s*sponsor',
    r'\bsponsorship\s*(available|offered)\b',
    r'\bwill\s*sponsor\b',
    r'\binternational\s*(candidates?|students?)\s*(welcome|encouraged)\b',
    r'\bf-?1\s*(opt|cpt)\s*(welcome|eligible)\b',
]

def analyze_visa_requirements(text: str, company_h1b: bool = False, company_lca: int = 0) -> Dict:
    """Analyze job text for visa requirements"""
    text_lower = text.lower()
    
    citizenship_required = any(re.search(p, text_lower) for p in CITIZENSHIP_PATTERNS)
    clearance_required = any(re.search(p, text_lower) for p in CLEARANCE_PATTERNS)
    h1b_mentioned = any(re.search(p, text_lower) for p in H1B_POSITIVE_PATTERNS)
    
    # Calculate OPT score
    score = 50
    if citizenship_required: score -= 50
    if clearance_required: score -= 40
    if h1b_mentioned: score += 30
    if company_h1b: score += 15
    if company_lca > 500: score += 10
    elif company_lca > 100: score += 5
    
    score = max(0, min(100, score))
    
    return {
        "citizenship_required": citizenship_required,
        "clearance_required": clearance_required,
        "h1b_mentioned": h1b_mentioned,
        "opt_score": score
    }

# ==================== SKILL EXTRACTOR ====================

SKILLS = {
    "cybersecurity": ["SIEM", "SOC", "Firewall", "IAM", "Penetration Testing", "Vulnerability", 
                      "Incident Response", "Threat", "CISSP", "Security+", "GRC", "Compliance",
                      "NIST", "ISO 27001", "Zero Trust", "EDR", "XDR"],
    "cloud": ["AWS", "Azure", "GCP", "Kubernetes", "Docker", "Terraform", "CloudFormation",
              "Lambda", "EC2", "S3", "DevOps", "CI/CD", "Jenkins", "Ansible"],
    "networking": ["TCP/IP", "DNS", "VPN", "BGP", "CCNA", "CCNP", "Cisco", "Palo Alto",
                   "Juniper", "SD-WAN", "Network Security"],
    "programming": ["Python", "Go", "Java", "JavaScript", "SQL", "Bash", "PowerShell"],
    "business": ["SQL", "Tableau", "Power BI", "Excel", "Agile", "Scrum", "Jira"]
}

def extract_skills(text: str) -> List[str]:
    """Extract skills from job text"""
    text_lower = text.lower()
    found = []
    for category, skills in SKILLS.items():
        for skill in skills:
            if skill.lower() in text_lower and skill not in found:
                found.append(skill)
    return found[:10]  # Top 10 skills

# ==================== CATEGORY CLASSIFIER ====================

def classify_job(title: str, description: str) -> List[str]:
    """Classify job into categories"""
    text = (title + " " + description).lower()
    categories = []
    
    if any(kw in text for kw in ["security", "cyber", "soc", "threat", "vulnerability", "iam", "grc"]):
        categories.append("cybersecurity")
    if any(kw in text for kw in ["cloud", "aws", "azure", "gcp", "devops", "sre", "kubernetes"]):
        categories.append("cloud")
    if any(kw in text for kw in ["network", "cisco", "firewall", "vpn", "noc"]):
        categories.append("networking")
    if any(kw in text for kw in ["business analyst", "data analyst", "product manager", "analytics"]):
        categories.append("business_analyst")
    if any(kw in text for kw in ["machine learning", "ml ", "ai ", "data scientist"]):
        categories.append("ai_ml")
    
    return categories if categories else ["other"]

# ==================== COLLECTORS ====================

async def collect_greenhouse_jobs(client: httpx.AsyncClient) -> List[Dict]:
    """Collect jobs from Greenhouse API"""
    all_jobs = []
    
    for token, info in GREENHOUSE_COMPANIES.items():
        try:
            print(f"  📡 Fetching {info['name']}...")
            url = f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true"
            resp = await client.get(url)
            
            if resp.status_code == 200:
                data = resp.json()
                jobs = data.get("jobs", [])
                
                for job in jobs:
                    title = job.get("title", "")
                    content = job.get("content", "")
                    
                    # Filter by keywords
                    text_lower = (title + " " + content).lower()
                    if not any(kw in text_lower for kw in TARGET_KEYWORDS):
                        continue
                    
                    # Analyze visa requirements
                    visa = analyze_visa_requirements(content, info["h1b"], info["lca"])
                    
                    # Skip citizenship required jobs
                    if visa["citizenship_required"]:
                        continue
                    
                    all_jobs.append({
                        "id": f"gh-{token}-{job['id']}",
                        "title": title,
                        "company": info["name"],
                        "company_id": token,
                        "industry": info["industry"],
                        "location": job.get("location", {}).get("name", "Unknown"),
                        "work_type": detect_work_type(title + " " + content),
                        "description": clean_html(content)[:1000],
                        "apply_url": job.get("absolute_url", ""),
                        "posted_date": job.get("updated_at", datetime.now().isoformat()),
                        "source": "Greenhouse",
                        "skills": extract_skills(content),
                        "categories": classify_job(title, content),
                        "h1b_sponsor_history": info["h1b"],
                        "h1b_lca_count": info["lca"],
                        "opt_score": visa["opt_score"],
                        "citizenship_required": visa["citizenship_required"],
                        "clearance_required": visa["clearance_required"],
                    })
                
                print(f"    ✅ {info['name']}: Found {len([j for j in all_jobs if j['company'] == info['name']])} relevant jobs")
            
            await asyncio.sleep(0.3)  # Rate limiting
            
        except Exception as e:
            print(f"    ❌ {info['name']}: Error - {e}")
    
    return all_jobs

async def collect_lever_jobs(client: httpx.AsyncClient) -> List[Dict]:
    """Collect jobs from Lever API"""
    all_jobs = []
    
    for slug, info in LEVER_COMPANIES.items():
        try:
            print(f"  📡 Fetching {info['name']}...")
            url = f"https://api.lever.co/v0/postings/{slug}"
            resp = await client.get(url)
            
            if resp.status_code == 200:
                jobs = resp.json()
                
                for job in jobs:
                    title = job.get("text", "")
                    desc = job.get("descriptionPlain", job.get("description", ""))
                    
                    # Filter by keywords
                    text_lower = (title + " " + desc).lower()
                    if not any(kw in text_lower for kw in TARGET_KEYWORDS):
                        continue
                    
                    # Analyze visa requirements
                    visa = analyze_visa_requirements(desc, info["h1b"], info["lca"])
                    
                    # Skip citizenship required jobs
                    if visa["citizenship_required"]:
                        continue
                    
                    # Get location
                    location = job.get("categories", {}).get("location", "Unknown")
                    
                    all_jobs.append({
                        "id": f"lv-{slug}-{job['id']}",
                        "title": title,
                        "company": info["name"],
                        "company_id": slug,
                        "industry": info["industry"],
                        "location": location,
                        "work_type": detect_work_type(title + " " + desc),
                        "description": clean_html(desc)[:1000],
                        "apply_url": job.get("hostedUrl", ""),
                        "posted_date": datetime.fromtimestamp(job.get("createdAt", 0) / 1000).isoformat() if job.get("createdAt") else datetime.now().isoformat(),
                        "source": "Lever",
                        "skills": extract_skills(desc),
                        "categories": classify_job(title, desc),
                        "h1b_sponsor_history": info["h1b"],
                        "h1b_lca_count": info["lca"],
                        "opt_score": visa["opt_score"],
                        "citizenship_required": visa["citizenship_required"],
                        "clearance_required": visa["clearance_required"],
                    })
                
                print(f"    ✅ {info['name']}: Found {len([j for j in all_jobs if j['company'] == info['name']])} relevant jobs")
            
            await asyncio.sleep(0.3)
            
        except Exception as e:
            print(f"    ❌ {info['name']}: Error - {e}")
    
    return all_jobs

def clean_html(html: str) -> str:
    """Remove HTML tags"""
    if not html:
        return ""
    clean = re.sub(r'<[^>]+>', ' ', html)
    clean = re.sub(r'\s+', ' ', clean)
    return clean.strip()

def detect_work_type(text: str) -> str:
    """Detect work type from text"""
    text_lower = text.lower()
    if "remote" in text_lower:
        return "remote"
    elif "hybrid" in text_lower:
        return "hybrid"
    return "onsite"

# ==================== MAIN COLLECTOR ====================

async def collect_all_jobs() -> Dict[str, Any]:
    """Collect jobs from all sources"""
    print("\n" + "="*60)
    print("🚀 MY AI AGENT - Live Job Collection")
    print("="*60)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Collect from Greenhouse
        print("📦 GREENHOUSE API (30 companies)")
        print("-" * 40)
        greenhouse_jobs = await collect_greenhouse_jobs(client)
        print(f"\n✅ Greenhouse Total: {len(greenhouse_jobs)} jobs\n")
        
        # Collect from Lever
        print("📦 LEVER API (10 companies)")
        print("-" * 40)
        lever_jobs = await collect_lever_jobs(client)
        print(f"\n✅ Lever Total: {len(lever_jobs)} jobs\n")
    
    # Combine all jobs
    all_jobs = greenhouse_jobs + lever_jobs
    
    # Sort by OPT score
    all_jobs.sort(key=lambda x: x["opt_score"], reverse=True)
    
    # Calculate stats
    stats = {
        "total_jobs": len(all_jobs),
        "greenhouse_jobs": len(greenhouse_jobs),
        "lever_jobs": len(lever_jobs),
        "h1b_sponsors": len(set(j["company"] for j in all_jobs if j["h1b_sponsor_history"])),
        "avg_opt_score": sum(j["opt_score"] for j in all_jobs) / len(all_jobs) if all_jobs else 0,
        "by_category": {},
        "collected_at": datetime.now().isoformat()
    }
    
    # Count by category
    for job in all_jobs:
        for cat in job["categories"]:
            stats["by_category"][cat] = stats["by_category"].get(cat, 0) + 1
    
    print("="*60)
    print("📊 COLLECTION SUMMARY")
    print("="*60)
    print(f"Total Jobs Collected: {stats['total_jobs']}")
    print(f"  - Greenhouse: {stats['greenhouse_jobs']}")
    print(f"  - Lever: {stats['lever_jobs']}")
    print(f"H-1B Sponsor Companies: {stats['h1b_sponsors']}")
    print(f"Average OPT Score: {stats['avg_opt_score']:.1f}")
    print(f"\nBy Category:")
    for cat, count in sorted(stats["by_category"].items(), key=lambda x: -x[1]):
        print(f"  - {cat}: {count}")
    print("="*60 + "\n")
    
    return {"jobs": all_jobs, "stats": stats}

def save_jobs(data: Dict, output_path: str = "collected_jobs.json"):
    """Save collected jobs to JSON file"""
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2, default=str)
    print(f"💾 Saved to {output_path}")

# ==================== RUN ====================

if __name__ == "__main__":
    result = asyncio.run(collect_all_jobs())
    save_jobs(result, "collected_jobs.json")
