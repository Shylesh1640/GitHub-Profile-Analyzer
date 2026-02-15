import os
import shutil
import tempfile
import logging
from datetime import datetime
from github import Github, GithubException
from .utils import clone_repo, cleanup_repo
from .scoring import compute_hiring_readiness, compute_role_fit
from .llm_client import LocalLLM

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class GitSightAnalyzer:
    def __init__(self, token=None, llm_model=None):
        self.github = Github(token)
        self.user = None
        self.llm = LocalLLM(model_name=llm_model) if llm_model else None

    def analyze_profile(self, username):
        """
        Main entry point for analyzing a GitHub profile.
        """
        try:
            self.user = self.github.get_user(username)
            logging.info(f"Analyzing profile: {username}")
        except GithubException as e:
            logging.error(f"Error fetching user {username}: {e}")
            return None

        profile_data = {
            "username": self.user.login,
            "profile_url": self.user.html_url,
            "analyzed_at": datetime.now().isoformat(),
            "total_repos_analyzed": 0,
            "primary_language": "Unknown",
            "languages_detected": set(),
            "repositories": []
        }

        repos = self.user.get_repos()
        for repo in repos:
            if repo.fork:
                continue  # Skip forks unless heavily modified (simplified for now)
            
            logging.info(f"Analyzing repo: {repo.name}")
            repo_analysis = self.analyze_repo(repo)
            profile_data["repositories"].append(repo_analysis)
            profile_data["languages_detected"].add(repo.language)

        profile_data["total_repos_analyzed"] = len(profile_data["repositories"])
        profile_data["languages_detected"] = list(profile_data["languages_detected"])
        
        # Determine primary language by frequency
        if profile_data["languages_detected"]:
            langs = [r['language'] for r in profile_data["repositories"] if r['language']]
            if langs:
                profile_data["primary_language"] = max(set(langs), key=langs.count)

        # Compute Higher Level Scores
        hiring_readiness = compute_hiring_readiness(profile_data)
        profile_data["hiring_readiness"] = hiring_readiness
        
        role_scores = compute_role_fit(profile_data)
        profile_data["role_scores"] = role_scores

        if self.llm:
            summary = self.llm.generate_profile_summary(profile_data, hiring_readiness)
            profile_data["llm_summary"] = summary

        return profile_data

    def analyze_repo(self, repo):
        """
        Analyzes a single repository.
        """
        analysis = {
            "repo_name": repo.name,
            "repo_url": repo.html_url,
            "language": repo.language,
            "stars": repo.stargazers_count,
            "forks": repo.forks_count,
            "description": repo.description,
            "composite_score": 0,  # Computed later
            "rating": "Unknown",   # Computed later
            "score_breakdown": {
                "code_structure": 0,
                "testing_ci": 0,
                "readme": 0,
                "project_value": 0, 
                "deployability": 0,
                "complexity": 0,
                "security": 0
            },
            "strengths": [],
            "weaknesses": [],
            "critical_flags": [],
            "improvement_suggestions": []
        }

        # Value Assessment (Stage 2G) - Basic Heuristics
        stars = repo.stargazers_count
        forks = repo.forks_count
        # Simple score based on popularity
        project_value = min(100, (stars * 2 + forks * 5))
        analysis["score_breakdown"]["project_value"] = project_value
        if project_value > 50:
             analysis["strengths"].append("High community interest (stars/forks)")

        # Clone and Deep Analyze
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = os.path.join(temp_dir, repo.name)
            if clone_repo(repo.clone_url, repo_path):
                # Analyze structure
                struct_score, struct_notes = self._analyze_structure(repo_path, repo.language)
                analysis["score_breakdown"]["code_structure"] = struct_score
                analysis["strengths"].extend(struct_notes.get("strengths", []))
                analysis["weaknesses"].extend(struct_notes.get("weaknesses", []))

                # Analyze README
                readme_score, readme_notes = self._analyze_readme(repo_path)
                analysis["score_breakdown"]["readme"] = readme_score
                if readme_notes:
                    analysis["strengths"].extend(readme_notes.get("strengths", []))
                    analysis["weaknesses"].extend(readme_notes.get("weaknesses", []))
                
                if readme_score > 70 and not readme_notes: # Fallback if no LLM notes
                    analysis["strengths"].append("Detailed README")
                elif readme_score <= 40 and not readme_notes:
                    analysis["weaknesses"].append("README lacks depth")

                # Analyze Testing
                test_score, test_notes = self._analyze_testing(repo_path)
                analysis["score_breakdown"]["testing_ci"] = test_score
                if test_score > 0:
                     analysis["strengths"].append("Testing infrastructure detected")
                else:
                     analysis["weaknesses"].append("No tests found")

                # Analyze Python Complexity (if Python)
                if repo.language == "Python":
                   comp_score = self._analyze_complexity_python(repo_path)
                   analysis["score_breakdown"]["complexity"] = comp_score
                else:
                   analysis["score_breakdown"]["complexity"] = 50 # Default middle ground

                # Security & Deployability
                sec_score, deploy_score = self._analyze_sec_deploy(repo_path)
                analysis["score_breakdown"]["security"] = sec_score
                analysis["score_breakdown"]["deployability"] = deploy_score

            else:
                logging.warning(f"Failed to clone {repo.name}. Skipping deep analysis.")
                analysis["critical_flags"].append("Clone failed - manual inspection required")

        # Calculate Composite Score
        analysis["composite_score"] = self._calculate_composite(analysis["score_breakdown"])
        analysis["rating"] = self._get_rating_label(analysis["composite_score"])
        
        return analysis

    def _analyze_structure(self, path, language):
        score = 50
        notes = {"strengths": [], "weaknesses": []}
        # Check for modularity
        src_dirs = ["src", "lib", "app", "core"]
        found_dirs = [d for d in src_dirs if os.path.exists(os.path.join(path, d))]
        if found_dirs:
            score += 20
            notes["strengths"].append(f"Structured project layout ({', '.join(found_dirs)})")
        
        # File count heuristic
        file_count = sum([len(files) for r, d, files in os.walk(path)])
        if file_count < 3:
            score -= 20
            notes["weaknesses"].append("Very small codebase (skeleton?)")
        elif file_count > 50:
            score += 10 # Complexity bonus? logic based on size

        return min(100, max(0, score)), notes

    def _analyze_readme(self, path):
        score = 0
        readme_path = None
        for f in os.listdir(path):
            if f.lower().startswith("readme"):
                readme_path = os.path.join(path, f)
                break
        
        if readme_path:
            score += 30 # Exists
            with open(readme_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read().lower()
                if len(content) > 500: score += 20 # Length
                if "install" in content: score += 10
                if "usage" in content: score += 10
                if "contributing" in content: score += 10
                if "license" in content: score += 10
                if "##" in content: score += 10 # Structure

                if self.llm:
                    try:
                        llm_analysis = self.llm.analyze_readme(content)
                        if llm_analysis and isinstance(llm_analysis, dict):
                            # Average the score
                            llm_score = llm_analysis.get('score', 0)
                            score = (score + llm_score) / 2
                            # Append notes
                            # analyzer.py expects the calling function to handle strength/weakness appending 
                            # but _analyze_readme returns (score, notes_dict)
                            # so we should add them to the return value
                            return min(100, int(score)), {
                                "strengths": llm_analysis.get("strengths", []), 
                                "weaknesses": llm_analysis.get("weaknesses", [])
                            }
                    except Exception as e:
                        logging.error(f"Error in LLM readme analysis: {e}")
        
        return min(100, score), {}

    def _analyze_testing(self, path):
        score = 0
        notes = []
        test_dirs = ["tests", "test", "__tests__", "spec"]
        for root, dirs, files in os.walk(path):
            if any(d in test_dirs for d in dirs):
                score += 40
                break
            # Check file names
            if any("test" in f.lower() for f in files):
                 score += 20
                 break
        
        # Check config files
        config_files = [".travis.yml", ".circleci", "Jenkinsfile", ".github/workflows", "pytest.ini", "jest.config.js"]
        for root, dirs, files in os.walk(path): # Simple check
             for f in files:
                 if f in config_files or ".github" in root:
                     score += 40
                     return min(100, score), {}
        
        return min(100, score), {}

    def _analyze_complexity_python(self, path):
        # Placeholder for Radon complexity check
        # Actually implement using Radon programmatically
        try:
            from radon.complexity import cc_visit
            file_count = 0
            total_cc = 0
            for root, dirs, files in os.walk(path):
                for file in files:
                    if file.endswith(".py"):
                        file_path = os.path.join(root, file)
                        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()
                            results = cc_visit(content)
                            for func in results:
                                total_cc += func.complexity
                                file_count += 1
            if file_count > 0:
                avg_cc = total_cc / file_count
                # Lower CC is better. Score 100 if avg_cc <= 5. Score 0 if avg_cc >= 20.
                score = max(0, 100 - (avg_cc - 5) * (100/15))
                return int(score)
        except Exception:
            pass
        return 50

    def _analyze_sec_deploy(self, path):
        sec_score = 80 # Assume good unless bad things found
        deploy_score = 0
        
        # Deploy signals
        deploy_files = ["Dockerfile", "docker-compose.yml", "Procfile", "requirements.txt", "package.json", ".vercelignore", "netlify.toml"]
        
        for root, dirs, files in os.walk(path):
            for file in files:
                if file in deploy_files:
                    deploy_score += 20
                if file == "Dockerfile": deploy_score += 30
                if file.endswith(".tf"): deploy_score += 30 # Terraform
        
        # Basic Security (Secrets)
        # VERY simple check strictly for demo
        # Real implementation needs regex for keys
        return min(100, sec_score), min(100, deploy_score)

    def _calculate_composite(self, breakdown):
        # Weighted formula from prompt
        # Code Quality & Structure: 25% | Testing & CI: 20% | Documentation: 15% | Value: 15% | Deploy: 10% | Complexity: 8% | Security: 7%
        score = (
            breakdown["code_structure"] * 0.25 +
            breakdown["testing_ci"] * 0.20 +
            breakdown["readme"] * 0.15 +
            breakdown["project_value"] * 0.15 +
            breakdown["deployability"] * 0.10 +
            breakdown["complexity"] * 0.08 +
            breakdown["security"] * 0.07
        )
        return int(score)

    def _get_rating_label(self, score):
        if score >= 85: return "⭐ Exceptional"
        if score >= 70: return "✅ Strong"
        if score >= 55: return "📈 Solid"
        if score >= 40: return "⚠️ Needs Work"
        return "🔴 Weak"

