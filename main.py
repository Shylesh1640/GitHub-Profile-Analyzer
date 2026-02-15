import argparse
import os
import sys
from dotenv import load_dotenv
from src.analyzer import GitSightAnalyzer
from src.report import ReportGenerator

def main():
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="GitSight - GitHub Profile Analyzer")
    parser.add_argument("profile", help="GitHub username or profile URL (e.g., 'torvalds' or 'https://github.com/torvalds')")
    parser.add_argument("--token", help="GitHub Personal Access Token (optional, overrides .env)", default=os.getenv("GITHUB_TOKEN"))
    parser.add_argument("--model", help="Ollama model name (e.g., llama3). If provided, enables AI analysis.", default=None)
    parser.add_argument("--out", help="Output directory for reports", default=".")
    
    args = parser.parse_args()
    
    raw_input = args.profile
    username = raw_input.rstrip("/").split("/")[-1].replace("@", "")
    
    print(f"🚀 Starting GitSight Analysis for user: {username}")
    if args.model:
        print(f"🧠 AI Analysis Enabled using model: {args.model}")
    
    analyzer = GitSightAnalyzer(token=args.token, llm_model=args.model)
    profile_data = analyzer.analyze_profile(username)
    
    if not profile_data:
        print("❌ Failed to retrieve profile. Please check the username and your internet connection.")
        sys.exit(1)
        
    if not profile_data.get("repositories"):
        print("⚠️ No public repositories found or all are forks (and skipped).")
        # Proceed to generate report anyway as "empty"
        
    print("📊 Analysis complete. Generating reports...")
    
    # Generate Reports
    reporter = ReportGenerator(profile_data)
    json_path = os.path.join(args.out, f"{username}_report.json")
    md_path = os.path.join(args.out, f"{username}_summary.md")
    
    reporter.generate_json(json_path)
    reporter.generate_markdown(md_path)
    
    print(f"✅ Report saved to: {json_path}")
    print(f"✅ Summary saved to: {md_path}")
    
    # Print a snippet of the summary to console
    print("\n--- Executive Summary ---\n")
    with open(md_path, "r", encoding="utf-8") as f:
        print(f.read())

if __name__ == "__main__":
    main()
