import ollama
import logging

# Set up logging for LLM interactions
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class LocalLLM:
    def __init__(self, model_name="llama3"):
        self.model = model_name
        self.client = ollama.Client(host='http://localhost:11434')

    def is_available(self):
        try:
            self.client.list()
            return True
        except Exception:
            return False

    def list_models(self):
        try:
            response = self.client.list()
            # Handle object response (newer versions)
            if hasattr(response, 'models'):
                return [m.model for m in response.models]
            # Handle dict response (older versions or compatibility)
            elif isinstance(response, dict) and 'models' in response:
                return [m['name'] for m in response['models']]
            return []
        except Exception as e:
            logging.error(f"Error listing models: {e}")
            return []

    def analyze_readme(self, readme_content):
        """
        Uses LLM to analyze README quality beyond simple keyword checks.
        """
        prompt = f"""
        You are a Senior Technical Recruiter. Analyze the following README content from a GitHub repository.
        Evaluate it on: Clarity, Completeness, and Technical Depth.
        
        README Content (truncated):
        {readme_content[:2000]}
        
        Output a concise JSON object with:
        - score (0-100)
        - strengths (list of strings)
        - weaknesses (list of strings)
        """
        try:
            response = self.client.chat(model=self.model, messages=[
                {'role': 'user', 'content': prompt}
            ], format='json')
            import json
            return json.loads(response['message']['content'])
        except Exception as e:
            logging.error(f"LLM README analysis failed: {e}")
            return None

    def generate_profile_summary(self, profile_data, readiness_score):
        """
        Generates a high-level executive summary of the developer based on the data.
        """
        prompt = f"""
        You are an elite Hiring Manager. Write a 2-paragraph executive summary for a developer with the following profile data:
        
        Profile Data:
        - Username: {profile_data.get('username')}
        - Hiring Readiness Score: {readiness_score.get('score')}/100 ({readiness_score.get('tier')})
        - Primary Language: {profile_data.get('primary_language')}
        - Total Repos: {profile_data.get('total_repos_analyzed')}
        - Top 3 Repos: {[r['repo_name'] for r in profile_data.get('repositories', [])[:3]]}
        - Role Fits: {profile_data.get('role_scores', {}).get('role_scores')}
        
        Focus on their strengths, potential fit for roles, and critical areas for improvement. Be professional and direct.
        """
        try:
            response = self.client.chat(model=self.model, messages=[
                {'role': 'user', 'content': prompt}
            ])
            return response['message']['content']
        except Exception as e:
            logging.error(f"LLM Summary generation failed: {e}")
            return "Summary generation failed due to LLM error."
