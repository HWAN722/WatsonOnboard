# WatsonOnboard - Quick Start Guide

Get up and running with WatsonOnboard in 5 minutes!

## Prerequisites

- Python 3.10 or higher
- IBM Watsonx account ([Sign up here](https://www.ibm.com/watsonx))
- Git (optional, for cloning repositories)

## Installation

### Step 1: Install WatsonOnboard

```bash
# Clone the repository
git clone https://github.com/yourusername/watson-onboard.git
cd watson-onboard

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install WatsonOnboard
pip install -e .
```

### Step 2: Configure Credentials

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your credentials
# Use your favorite text editor (nano, vim, notepad, etc.)
nano .env
```

Add your IBM Watsonx credentials:

```bash
WATSONX_API_KEY=your_api_key_here
WATSONX_PROJECT_ID=your_project_id_here
WATSONX_URL=https://us-south.ml.cloud.ibm.com
```

**Where to find your credentials:**
1. Log in to [IBM Cloud](https://cloud.ibm.com)
2. Navigate to your Watsonx project
3. Go to "Manage" → "Access (IAM)" → "API keys"
4. Create or copy your API key
5. Find your Project ID in the project settings

### Step 3: Verify Installation

```bash
# Check version
watson-onboard version

# Should output:
# WatsonOnboard - Legacy Code Onboarding Assistant
# Version: 0.1.0
# Powered by IBM Watsonx
```

## Your First Analysis

### Analyze a Repository

Let's analyze a sample repository:

```bash
# Analyze a local repository
watson-onboard analyze /path/to/your/repo --output onboarding_report.md

# Example with a Python project
watson-onboard analyze ~/projects/my-python-app --output my-app-report.md
```

**What happens:**
1. ✅ Scans all files in the repository
2. ✅ Parses code and extracts structure
3. ✅ Builds dependency graph
4. ✅ Calculates file importance
5. ✅ Generates embeddings for Q&A
6. ✅ Creates comprehensive report

**Expected output:**
```
Analyzing repository: /path/to/your/repo
Scanning repository files...
Found 150 files
Parsing code and extracting metadata...
Parsed 120 files
Building dependency graph...
Calculating file importance rankings...
Generating embeddings for Q&A...
Indexed 450 code chunks
Generating onboarding report...
Report generation complete!
✓ Report saved to: onboarding_report.md
```

### View the Report

```bash
# Open in your default markdown viewer
# On macOS:
open onboarding_report.md

# On Linux:
xdg-open onboarding_report.md

# On Windows:
start onboarding_report.md

# Or use any text editor
code onboarding_report.md  # VS Code
```

## Interactive Q&A

### Ask Questions About Your Codebase

After analyzing a repository, you can ask questions:

```bash
# Interactive mode during analysis
watson-onboard analyze /path/to/repo --interactive

# Or ask questions separately
watson-onboard ask "How does authentication work in this codebase?"
watson-onboard ask "What are the main entry points?"
watson-onboard ask "Explain the database connection logic"
```

**Example session:**
```
❓ Your question: How does authentication work?

🤔 Thinking...

💡 Answer:
The authentication system uses JWT tokens. The main authentication
logic is in `src/auth/jwt_handler.py`. When a user logs in:

1. Credentials are validated in `validate_credentials()`
2. A JWT token is generated using `create_access_token()`
3. The token is stored in the session
4. Protected routes check the token using `verify_token()`

Key files:
- src/auth/jwt_handler.py (lines 15-45)
- src/middleware/auth_middleware.py (lines 20-35)

❓ Your question: exit
👋 Goodbye!
```

## Semantic Code Search

Search for specific functionality:

```bash
# Search for database-related code
watson-onboard search "database connection logic" --top-k 5

# Search for authentication code
watson-onboard search "user authentication" --top-k 10

# Search for API endpoints
watson-onboard search "REST API endpoints" --top-k 5
```

**Example output:**
```
🔍 Found 5 results:

Rank  File                          Score   Preview
1     src/db/connection.py          0.892   def create_connection(): """Establishes database connection..."""
2     src/db/pool.py                0.845   class ConnectionPool: """Manages database connection pool..."""
3     src/config/database.py        0.823   DATABASE_URL = os.getenv("DATABASE_URL")...
4     src/models/base.py            0.801   from sqlalchemy import create_engine...
5     src/utils/db_helper.py        0.789   def get_db_session(): """Returns database session..."""
```

## Using the REST API

### Start the API Server

```bash
# Start server on default port (8000)
watson-onboard serve

# Or specify port and enable auto-reload
watson-onboard serve --port 8080 --reload
```

**Server output:**
```
Starting WatsonOnboard API server...
Host: 0.0.0.0
Port: 8000
Reload: False

INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### Access API Documentation

Open your browser and visit:
- **Interactive docs**: http://localhost:8000/docs
- **Alternative docs**: http://localhost:8000/redoc
- **Health check**: http://localhost:8000/health

### Make API Requests

```bash
# Using curl
curl -X POST "http://localhost:8000/api/analyze" \
  -H "Content-Type: application/json" \
  -d '{"repo_path": "/path/to/repo"}'

# Using Python
import httpx

response = httpx.post(
    "http://localhost:8000/api/analyze",
    json={"repo_path": "/path/to/repo"}
)
job_id = response.json()["job_id"]
print(f"Job ID: {job_id}")
```

## Running Demo Scripts

Try the included demo scripts:

```bash
# Full analysis demo
python demo/analyze_sample_repo.py

# Interactive Q&A demo
python demo/interactive_qa.py

# API usage demo (requires server running)
python demo/api_demo.py
```

## Common Use Cases

### 1. Onboarding New Team Members

```bash
# Generate comprehensive onboarding report
watson-onboard analyze /path/to/project --output team-onboarding.md

# Share the report with new team members
# They can also use the Q&A feature to ask questions
```

### 2. Understanding Legacy Code

```bash
# Analyze legacy codebase
watson-onboard analyze /path/to/legacy-app --interactive

# Ask questions like:
# - "What are the main components?"
# - "How does the system handle errors?"
# - "What are the external dependencies?"
```

### 3. Code Review Preparation

```bash
# Analyze before code review
watson-onboard analyze /path/to/feature-branch

# Search for specific patterns
watson-onboard search "error handling patterns"
watson-onboard search "database transactions"
```

### 4. Documentation Generation

```bash
# Generate documentation for multiple projects
for project in project1 project2 project3; do
  watson-onboard analyze ~/projects/$project --output docs/${project}-guide.md
done
```

### 5. CI/CD Integration

```bash
# Add to your CI pipeline
# .github/workflows/documentation.yml
- name: Generate Onboarding Docs
  run: |
    pip install watson-onboard
    watson-onboard analyze . --output docs/ONBOARDING.md
    git add docs/ONBOARDING.md
    git commit -m "Update onboarding documentation"
```

## Tips & Tricks

### 1. Speed Up Analysis

```bash
# Use cache for repeated analyses
export CACHE_DIR=.watson-cache
watson-onboard analyze /path/to/repo
```

### 2. Customize Output

```bash
# Generate JSON output for programmatic use
watson-onboard analyze /path/to/repo --format json --output report.json
```

### 3. Focus on Specific Files

```bash
# Analyze only Python files
watson-onboard analyze /path/to/repo --file-pattern "*.py"
```

### 4. Verbose Logging

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
watson-onboard analyze /path/to/repo
```

### 5. Batch Processing

```bash
# Analyze multiple repositories
cat repos.txt | while read repo; do
  watson-onboard analyze "$repo" --output "reports/$(basename $repo).md"
done
```

## Troubleshooting

### Issue: "Import errors"

**Solution:**
```bash
pip install -e .
```

### Issue: "Watsonx API authentication failed"

**Solution:**
1. Check your `.env` file has correct credentials
2. Verify API key is active in IBM Cloud
3. Check project ID is correct

### Issue: "No indexed codebase found"

**Solution:**
```bash
# Run analysis first to index the codebase
watson-onboard analyze /path/to/repo
```

### Issue: "Server not responding"

**Solution:**
```bash
# Make sure server is running
watson-onboard serve --port 8000

# Check if port is already in use
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows
```

### Issue: "Out of memory"

**Solution:**
- Analyze smaller repositories first
- Increase system memory
- Use `--batch-size` parameter (if available)

## Next Steps

Now that you're up and running:

1. **Explore the Report**: Review the generated onboarding documentation
2. **Try Q&A**: Ask questions about your codebase
3. **Use the API**: Integrate with your tools
4. **Customize**: Modify prompts and templates
5. **Contribute**: Check out [CONTRIBUTING.md](CONTRIBUTING.md)

## Getting Help

- **Documentation**: See [README.md](README.md) for detailed docs
- **Examples**: Check the `demo/` directory
- **Issues**: Report bugs on GitHub Issues
- **Questions**: Ask in GitHub Discussions

## Resources

- [Full Documentation](README.md)
- [API Reference](http://localhost:8000/docs)
- [Contributing Guide](CONTRIBUTING.md)
- [Project Summary](PROJECT_SUMMARY.md)
- [IBM Watsonx Docs](https://www.ibm.com/docs/en/watsonx)

---

**Happy Onboarding! 🚀**

Need help? Open an issue or check the documentation.