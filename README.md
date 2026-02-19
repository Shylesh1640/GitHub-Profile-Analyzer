# GitHub-Profile-Analyzer(GitSight)

**Elite GitHub Profile Analyzer & Hiring Readiness Evaluator**

## Features
- Analyze any GitHub profile by username or URL
- AI-powered analysis using local Ollama models
- Generate JSON and Markdown reports
- Web UI (Streamlit) and CLI support

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/GitHub-Profile-Analyzer.git
   cd GitHub-Profile-Analyzer
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables (optional):**
   Create a `.env` file in the project root:
   ```
   GITHUB_TOKEN=your_github_personal_access_token
   ```

4. **Set up Ollama for AI analysis (optional):**
   - Install [Ollama](https://ollama.ai/)
   - Start the Ollama server: `ollama serve`
   - Pull a model: `ollama pull llama3`

## How to Run

### Option 1: Web UI (Streamlit)
```bash
streamlit run app.py
```
Then open your browser to `http://localhost:8501`

### Option 2: Command Line
```bash
python main.py <github_username_or_url>
```

**Examples:**
```bash
# Basic usage
python main.py torvalds

# With GitHub URL
python main.py https://github.com/torvalds

# With AI analysis
python main.py torvalds --model llama3

# With custom output directory
python main.py torvalds --out ./reports

# With GitHub token
python main.py torvalds --token YOUR_GITHUB_TOKEN
```

**CLI Arguments:**
| Argument | Description |
|----------|-------------|
| `profile` | GitHub username or profile URL (required) |
| `--token` | GitHub Personal Access Token (optional) |
| `--model` | Ollama model name for AI analysis (optional) |
| `--out` | Output directory for reports (default: current directory) |

## Output
- `<username>_report.json` - Detailed JSON report
- `<username>_summary.md` - Markdown summary