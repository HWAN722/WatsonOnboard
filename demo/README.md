# WatsonOnboard Demo Scripts

This directory contains demonstration scripts that showcase the capabilities of WatsonOnboard.

## Prerequisites

Before running the demos, ensure you have:

1. **Installed WatsonOnboard**:
   ```bash
   pip install -e .
   ```

2. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your IBM Watsonx credentials
   ```

3. **A sample repository to analyze** (or use your own project)

## Demo Scripts

### 1. Repository Analysis Demo

**File**: `analyze_sample_repo.py`

Demonstrates the complete analysis workflow:
- Scans repository files
- Parses code and extracts metadata
- Builds dependency graph
- Calculates file importance rankings
- Generates comprehensive onboarding report

**Usage**:
```bash
python demo/analyze_sample_repo.py
```

You'll be prompted to enter:
- Path to the repository to analyze
- Output file path for the report

**Example**:
```
Enter the path to the repository to analyze: /path/to/your/repo
Enter output file path (default: onboarding_report.md): my_report.md
```

### 2. Interactive Q&A Demo

**File**: `interactive_qa.py`

Demonstrates the Q&A capabilities:
- Loads indexed codebase from vector store
- Accepts user questions
- Retrieves relevant code chunks
- Generates answers using Watsonx

**Usage**:
```bash
# First, run the analysis demo to index a codebase
python demo/analyze_sample_repo.py

# Then run the Q&A demo
python demo/interactive_qa.py
```

**Example Questions**:
- "How does authentication work in this codebase?"
- "What are the main entry points?"
- "Explain the database connection logic"
- "What design patterns are used?"

### 3. REST API Demo

**File**: `api_demo.py`

Demonstrates the REST API endpoints:
- Starts analysis jobs
- Monitors job status
- Downloads reports
- Queries the codebase
- Performs semantic search

**Usage**:
```bash
# Terminal 1: Start the API server
watson-onboard serve --port 8000

# Terminal 2: Run the demo
python demo/api_demo.py
```

The demo will guide you through:
1. Health check
2. Starting an analysis job
3. Monitoring job progress
4. Downloading the report
5. Asking questions
6. Semantic search
7. Listing all jobs

## Using the CLI Directly

After installation, you can use the `watson-onboard` command directly:

### Analyze a Repository
```bash
watson-onboard analyze /path/to/repo --output report.md
```

### Interactive Analysis
```bash
watson-onboard analyze /path/to/repo --interactive
```

### Ask Questions
```bash
watson-onboard ask "How does the authentication system work?"
```

### Semantic Search
```bash
watson-onboard search "database connection logic" --top-k 5
```

### Start API Server
```bash
watson-onboard serve --port 8000 --reload
```

## Tips

1. **Start Small**: Begin with a small repository to test the system
2. **Check Logs**: Use `--verbose` flag for detailed logging
3. **API Documentation**: Visit `http://localhost:8000/docs` for interactive API docs
4. **Customize Prompts**: Edit `src/watsonx/prompts.py` to customize AI responses
5. **Vector Store**: The vector store persists in `./chroma_db` directory

## Troubleshooting

### "No indexed codebase found"
Run the analysis demo first to index a repository.

### "Import errors"
Make sure you've installed the package:
```bash
pip install -e .
```

### "Watsonx API errors"
Check your `.env` file has valid credentials:
- `WATSONX_API_KEY`
- `WATSONX_PROJECT_ID`
- `WATSONX_URL`

### "Server not responding"
Ensure the API server is running:
```bash
watson-onboard serve --port 8000
```

## Next Steps

After running the demos:

1. **Explore the Generated Report**: Review the markdown report for insights
2. **Try Different Repositories**: Analyze various codebases to see different patterns
3. **Customize Prompts**: Modify the AI prompts for your specific needs
4. **Integrate with CI/CD**: Use the API to automate onboarding documentation
5. **Extend Functionality**: Add custom analyzers or report sections

## Support

For issues or questions:
- Check the main README.md
- Review the API documentation at `/docs`
- Open an issue on GitHub