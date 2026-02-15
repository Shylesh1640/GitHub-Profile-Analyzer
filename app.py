import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv
from src.analyzer import GitSightAnalyzer
from src.report import ReportGenerator

from src.llm_client import LocalLLM

# Load environment
load_dotenv()

st.set_page_config(page_title="GitSight - GitHub Profile Analyzer", layout="wide")

st.title("GitSight 👁️")
st.markdown("**Elite GitHub Profile Analyzer & Hiring Readiness Evaluator**")

# Sidebar for Token and Model
st.sidebar.header("Configuration")
token = st.sidebar.text_input("GitHub Token (Optional but Recommended)", type="password", help="Use a token to avoid rate limits.")
if not token:
    token = os.getenv("GITHUB_TOKEN")

# Model Selection
llm_client = LocalLLM()
available_models = llm_client.list_models()
selected_model = None

if available_models:
    selected_model = st.sidebar.selectbox("Select Ollama Model (Local)", available_models, index=0)
    st.sidebar.success(f"Using model: {selected_model}")
else:
    st.sidebar.warning("Ollama not detected or no models found. Falling back to heuristic mode.")
    st.sidebar.info("Ensure Ollama is running (`ollama serve`) and you have pulled a model (e.g. `ollama pull llama3`).")

# Input
profile_input = st.text_input("Enter GitHub Username or Profile URL", placeholder="e.g. torvalds, https://github.com/torvalds")

# Analyze button logic
if st.button("Analyze Profile"):
    if not profile_input:
        st.error("Please enter a username or URL.")
    else:
        username = profile_input.rstrip("/").split("/")[-1].replace("@", "")
        
        with st.spinner(f"Analyzing {username}... This may take a minute (analyzing repos & structure)..."):
            analyzer = GitSightAnalyzer(token=token if token else None, llm_model=selected_model)
            try:
                data = analyzer.analyze_profile(username)
                if data:
                    st.session_state['profile_data'] = data
                    st.success("Analysis Complete!")
                else:
                    st.error("Failed to fetch profile. Check username or API limits.")
            except Exception as e:
                 st.error(f"Error: {e}")

# Display Logic (outside button callback)
if 'profile_data' in st.session_state:
    data = st.session_state['profile_data']
    
    # Display Results
    readiness = data.get("hiring_readiness", {})
    st.header(f"Hiring Readiness: {readiness.get('score', 0)}/100")
    st.subheader(f"{readiness.get('tier_label', '')} - {readiness.get('tier', '')}")
    
    # Columns for Role Fit
    col1, col2, col3 = st.columns(3)
    roles = data.get("role_scores", {}).get("role_scores", {}) # Fix structure access
    
    with col1:
        st.metric("ML Engineer", f"{roles.get('ml_engineer', {}).get('score', 0)}%", roles.get('ml_engineer', {}).get('fit_label', 'N/A'))
    with col2:
        st.metric("Backend Engineer", f"{roles.get('backend_engineer', {}).get('score', 0)}%", roles.get('backend_engineer', {}).get('fit_label', 'N/A'))
    with col3:
        st.metric("SRE", f"{roles.get('sre', {}).get('score', 0)}%", roles.get('sre', {}).get('fit_label', 'N/A'))

    st.divider()
    
    # Repository Table
    st.subheader("Repository Analysis")
    repos = data.get("repositories", [])
    if repos:
        # Create DataFrame for display
        display_data = []
        for r in repos:
            display_data.append({
                "Repository": r["repo_name"],
                "Language": r["language"],
                "Score": r["composite_score"],
                "Rating": r["rating"]
            })
        
        df = pd.DataFrame(display_data)
        st.dataframe(df.sort_values("Score", ascending=False), use_container_width=True)
        
        # Detail View
        repo_names = [r['repo_name'] for r in repos]
        repo_choice = st.selectbox("Select Repository for Deep Dive", repo_names)
        
        selected_repo = next((r for r in repos if r['repo_name'] == repo_choice), None)
        
        if selected_repo:
            st.markdown(f"### detailed Analysis: {selected_repo['repo_name']}")
            st.write(f"**Rating:** {selected_repo['rating']}")
            st.write(f"**Description:** {selected_repo['description']}")
            
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("#### Score Breakdown")
                st.json(selected_repo["score_breakdown"])
            with c2:
                st.markdown("#### Insights")
                st.markdown("**Strengths:**")
                for s in selected_repo.get("strengths", []): st.write(f"✅ {s}")
                st.markdown("**Weaknesses & Gaps:**")
                for w in selected_repo.get("weaknesses", []): st.write(f"⚠️ {w}")

    # Download Report
    st.divider()
    reporter = ReportGenerator(data)
    json_str = reporter.generate_json("report.json") # Saves locally
    with open("report.json", "r") as f:
         st.download_button("Download JSON Report", f, file_name=f"{data.get('username', 'profile')}_report.json", mime="application/json")

