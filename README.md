# WatsonOnboard - Legacy Code Onboarding Assistant

A CLI and Web tool powered by IBM Watsonx that ingests any Git repository and produces a complete onboarding package, helping new developers understand codebases in minutes instead of weeks.

## Features

- 🔍 **Automated Code Analysis**: Scans repositories and extracts structure, dependencies, and metadata
- 🗺️ **Architecture Mapping**: Generates visual dependency graphs and architecture diagrams
- 📚 **Smart Documentation**: Creates comprehensive onboarding guides with reading lists
- 💬 **Interactive Q&A**: Ask questions about the codebase using natural language
- 🤖 **Powered by IBM Watsonx**: Leverages advanced LLMs for code understanding

## Project Structure

```
watson-onboard/
├── src/
│   ├── scanner/          # Repository scanning and code analysis
│   ├── graph/            # Dependency graph building and ranking
│   ├── watsonx/          # IBM Watsonx integration
│   ├── report/           # Documentation generation
│   ├── qa/               # Vector store and Q&A system
│   ├── api/              # FastAPI backend
│   └── cli/              # Command-line interface
├── tests/                # Test suite
└── scripts/              # Utility scripts
```

## Prerequisites

- Python 3.11 or higher
- IBM Watsonx API credentials
- Git

## Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd WatsonOnboard
```

### 2. Create a virtual environment

```bash
python -m venv .venv

# On Windows
.venv\Scripts\activate

# On macOS/Linux
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy `.env.example` to `.env` and update with your credentials:

```bash
cp .env.example .env
```

Edit `.env` and add your IBM Watsonx credentials:

```env
WATSONX_API_KEY=your-api-key-here
WATSONX_URL=your-watsonx-url
WATSONX_PROJECT_ID=your-project-id
```

## Usage

### Using PowerShell Scripts (Windows)

```powershell
# Install dependencies
.\scripts\run_local.ps1 install

# Run tests
.\scripts\run_local.ps1 test

# Start API server
.\scripts\run_local.ps1 run

# Format code
.\scripts\run_local.ps1 format

# Run linters
.\scripts\run_local.ps1 lint

# Clean cache
.\scripts\run_local.ps1 clean
```

### Using Makefile (macOS/Linux)

```bash
# Install dependencies
make install

# Run tests
make test

# Start API server
make run

# Format code
make format

# Run linters
make lint

# Clean cache
make clean
```

### API Server

Start the FastAPI server:

```bash
uvicorn src.api.main:app --reload
```

Access the API documentation at: http://localhost:8000/docs

### CLI (Coming Soon)

```bash
# Analyze a repository
watson-onboard analyze /path/to/repo

# Ask questions about the codebase
watson-onboard ask "Where is authentication handled?"

# Start interactive mode
watson-onboard serve
```

## API Endpoints

- `GET /` - Root endpoint with API information
- `GET /health` - Health check and Watsonx connectivity status
- `POST /analyze` - Analyze a repository (coming soon)
- `POST /query` - Query the codebase (coming soon)

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/integration/test_api_health.py
```

### Code Quality

```bash
# Format code
black src tests

# Lint code
ruff check src tests

# Type checking
mypy src
```

## Tech Stack

- **Language**: Python 3.11+
- **Backend**: FastAPI + Uvicorn
- **CLI**: Typer
- **Code Parsing**: tree-sitter
- **Graph Analysis**: NetworkX
- **Vector DB**: ChromaDB
- **LLM**: IBM Watsonx (Granite, Llama models)
- **Testing**: pytest, pytest-asyncio
- **Code Quality**: ruff, black, mypy

## Project Status

🚧 **Phase 0 - Project Setup**: ✅ Complete
- Project structure created
- Configuration management implemented
- Basic API with health endpoint
- Test infrastructure set up

📋 **Next Phases**:
- Phase 1: Repository Scanner Module
- Phase 2: Dependency Graph Builder
- Phase 3: Watsonx Integration Layer
- Phase 4: Summary & Report Generator
- Phase 5: Vector Store + Interactive Q&A
- Phase 6: REST API (Backend)
- Phase 7: CLI Interface

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linters
5. Submit a pull request

## License

[Add your license here]

## Support

For issues and questions, please open an issue on GitHub.