
def compute_hiring_readiness(profile_data):
    """
    Computes the Hiring Readiness Score (0-100) based on the aggregated profile data.
    Formula:
    hiring_readiness = (
      avg_repo_score * 0.35 +
      best_3_repos_avg * 0.25 +
      portfolio_diversity * 0.15 +
      testing_ci_presence * 0.10 +
      deployability_presence * 0.10 +
      security_baseline * 0.05
    )
    """
    repos = profile_data.get("repositories", [])
    if not repos:
        return {
            "score": 0,
            "tier": "🔴 Not Ready",
            "tier_label": "Foundational gaps; focus on fundamentals first"
        }

    # Extract scores
    repo_scores = [r["composite_score"] for r in repos]
    avg_repo_score = sum(repo_scores) / len(repo_scores) if repo_scores else 0
    
    # Best 3 repos
    best_3 = sorted(repo_scores, reverse=True)[:3]
    best_3_repos_avg = sum(best_3) / len(best_3) if best_3 else 0

    # Portfolio Diversity (check languages and topics)
    langs = load_languages(repos)
    portfolio_diversity = min(100, len(langs) * 20) # Simple heuristic: 5 languages = 100%

    # Testing & CI Presence (% of repos with tests/CI > 0)
    testing_ci_presence = sum(1 for r in repos if r["score_breakdown"]["testing_ci"] > 0) / len(repos) * 100

    # Deployability Presence
    deployability_presence = sum(1 for r in repos if r["score_breakdown"]["deployability"] > 0) / len(repos) * 100

    # Security Baseline (absence of critical issues)
    # Start at 100, deduct for critical flags
    security_baseline = 100 
    for r in repos:
        if r.get("critical_flags"): # If ANY repo has critical flags
             security_baseline -= 20
    security_baseline = max(0, security_baseline)

    # Compute Final Score
    score = (
        avg_repo_score * 0.35 +
        best_3_repos_avg * 0.25 +
        portfolio_diversity * 0.15 +
        testing_ci_presence * 0.10 +
        deployability_presence * 0.10 +
        security_baseline * 0.05
    )
    
    final_score = int(score)
    
    # Determine Tier
    tier = "Unknown"
    if final_score >= 85: tier = "🏆 Hire-Ready"
    elif final_score >= 70: tier = "✅ Competitive"
    elif final_score >= 55: tier = "📈 Developing"
    elif final_score >= 40: tier = "⚠️ Early Stage"
    else: tier = "🔴 Not Ready"

    return {
        "score": final_score,
        "tier": tier,
        "tier_label": get_tier_label(tier)
    }

def compute_role_fit(profile_data):
    """
    Computes fit scores for ML, Backend, and SRE roles.
    """
    # Simple logic based on language and keywords for now
    # Real implementation would re-weight repo scores based on role affinity
    # Here we just check for language presence and keywords in top repos
    
    roles = {
        "ml_engineer": {"score": 0, "fit_label": ""},
        "backend_engineer": {"score": 0, "fit_label": ""},
        "sre": {"score": 0, "fit_label": ""}
    }
    
    repos = profile_data.get("repositories", [])
    if not repos: return {"role_scores": roles}

    # ML Fit
    ml_keywords = ["model", "train", "dataset", "jupyter", "pandas", "numpy", "sklearn", "tensorflow", "pytorch"]
    ml_score = 0
    for r in repos:
        if r["language"] == "Jupyter Notebook" or r["language"] == "Python":
            ml_score += 10
        if any(k in r["description"].lower() for k in ml_keywords if r["description"]):
            ml_score += 15
    roles["ml_engineer"]["score"] = min(100, ml_score)
    roles["ml_engineer"]["fit_label"] = get_fit_label(roles["ml_engineer"]["score"])

    # Backend Fit
    be_keywords = ["api", "server", "database", "sql", "rest", "graphql", "docker", "auth"]
    be_score = 0
    for r in repos:
        if r["language"] in ["Python", "Go", "Java", "JavaScript", "TypeScript", "Rust"]:
            be_score += 10
        if any(k in r["description"].lower() for k in be_keywords if r["description"]):
            be_score += 15
        be_score += r["score_breakdown"]["code_structure"] / 10 # Bonus for structure
    roles["backend_engineer"]["score"] = min(100, int(be_score))
    roles["backend_engineer"]["fit_label"] = get_fit_label(roles["backend_engineer"]["score"])

    # SRE Fit
    sre_keywords = ["kubernetes", "docker", "terraform", "ansible", "cloud", "aws", "gcp", "azure", "monitor", "prometheus"]
    sre_score = 0
    for r in repos:
         if any(k in r["description"].lower() for k in sre_keywords if r["description"]):
            sre_score += 20
         sre_score += r["score_breakdown"]["deployability"] / 2 # Strong weight on deployability
    roles["sre"]["score"] = min(100, int(sre_score))
    roles["sre"]["fit_label"] = get_fit_label(roles["sre"]["score"])
    
    return {"role_scores": roles}

def get_fit_label(score):
    if score > 80: return "High Fit"
    if score > 50: return "Moderate Fit"
    return "Low Fit"

def get_tier_label(tier):
    labels = {
        "🏆 Hire-Ready": "Strong candidate; portfolio speaks for itself",
        "✅ Competitive": "Solid candidate; minor gaps to address",
        "📈 Developing": "Promising; needs focused improvement in 2-3 areas",
        "⚠️ Early Stage": "Real potential; portfolio needs significant work",
        "🔴 Not Ready": "Foundational gaps; focus on fundamentals first"
    }
    return labels.get(tier, "")

def load_languages(repos):
    s = set()
    for r in repos:
        if r["language"]: s.add(r["language"])
    return list(s)
