import json
import os

class ReportGenerator:
    def __init__(self, data):
        self.data = data

    def generate_json(self, output_path="report.json"):
        """Saves the full structured report to a JSON file."""
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2, default=str)
        return output_path

    def generate_markdown(self, output_path="SUMMARY.md"):
        """Generates the human-readable executive summary."""
        profile = self.data["profile_data"] if "profile_data" in self.data else self.data
        username = profile.get("username", "Unknown")
        readiness = self.data.get("hiring_readiness", {})
        roles = self.data.get("role_scores", {}).get("role_scores", {})
        repos = profile.get("repositories", [])
        
        # Sort repos by score
        sorted_repos = sorted(repos, key=lambda x: x.get("composite_score", 0), reverse=True)
        top_repos = sorted_repos[:3]

        md = f"""# 📊 GitHub Profile Analysis — @{username}

**Hiring Readiness Score: {readiness.get('score', 0)}/100 — {readiness.get('tier', 'Unknown')}**

### 🔍 Quick Overview
{profile.get('llm_summary', f"User @{username} has {len(repos)} public repositories. Primary language: {profile.get('primary_language', 'N/A')}.")}
{readiness.get('tier_label', '')}

### 🏅 Repository Highlights
"""
        for r in top_repos:
            md += f"- **[{r['repo_name']}]({r['repo_url']})**: {r.get('composite_score', 0)}/100 ({r.get('rating', '')}) - {r.get('description', 'No description')} \n"

        md += f"""
### 💼 Role Fit
- **ML Engineer**: {roles.get('ml_engineer', {}).get('score', 0)}/100 — {roles.get('ml_engineer', {}).get('fit_label', '')}
- **Backend Engineer**: {roles.get('backend_engineer', {}).get('score', 0)}/100 — {roles.get('backend_engineer', {}).get('fit_label', '')}
- **SRE**: {roles.get('sre', {}).get('score', 0)}/100 — {roles.get('sre', {}).get('fit_label', '')}

### ✅ What's Working
"""
        # Aggregate strengths
        all_strengths = []
        for r in repos:
            all_strengths.extend(r.get("strengths", []))
        
        # Dedupe and pick top 5
        unique_strengths = list(set(all_strengths))[:5]
        if not unique_strengths:
            md += "- No major strengths detected automatically.\n"
        for s in unique_strengths:
            md += f"- {s}\n"

        md += """
### ⚠️ What Needs Improvement
"""
        # Aggregate weaknesses
        all_weaknesses = []
        for r in repos:
            all_weaknesses.extend(r.get("weaknesses", []))
        
        unique_weaknesses = list(set(all_weaknesses))[:5]
        if not unique_weaknesses:
             md += "- No major weaknesses detected automatically.\n"
        for w in unique_weaknesses:
            md += f"- {w}\n"

        md += """
### 🚀 Top Actions to Increase Hiring Readiness
"""
        # Generate generic actions if score is low
        if readiness.get('score', 0) < 50:
            md += "1. Add unit tests (pytest/jest) to your top projects.\n"
            md += "2. Improving README documentation with installation instructions.\n"
            md += "3. Setup a CI pipeline (GitHub Actions) for your main repo.\n"
        else:
             md += "1. Continue maintaining high code quality.\n"

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(md)
        
        return output_path
