"""Setup configuration for WatsonOnboard."""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

setup(
    name="watson-onboard",
    version="0.1.0",
    description="Legacy Code Onboarding Assistant powered by IBM Watsonx",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/yourusername/watson-onboard",
    packages=find_packages(exclude=["tests", "tests.*"]),
    python_requires=">=3.10",
    install_requires=[
        "fastapi>=0.104.0",
        "uvicorn[standard]>=0.24.0",
        "pydantic>=2.5.0",
        "pydantic-settings>=2.1.0",
        "python-dotenv>=1.0.0",
        "httpx>=0.25.0",
        "ibm-watsonx-ai>=0.2.0",
        "chromadb>=0.4.18",
        "tree-sitter>=0.20.4",
        "tree-sitter-python>=0.20.4",
        "tree-sitter-javascript>=0.20.3",
        "tree-sitter-java>=0.20.2",
        "tree-sitter-go>=0.20.0",
        "networkx>=3.2.1",
        "gitpython>=3.1.40",
        "typer>=0.9.0",
        "rich>=13.7.0",
        "structlog>=23.2.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.3",
            "pytest-asyncio>=0.21.1",
            "pytest-cov>=4.1.0",
            "black>=23.11.0",
            "ruff>=0.1.6",
            "mypy>=1.7.1",
            "pre-commit>=3.5.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "watson-onboard=src.cli.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Documentation",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    keywords="code-analysis onboarding documentation watsonx ibm ai llm",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/watson-onboard/issues",
        "Source": "https://github.com/yourusername/watson-onboard",
    },
)

# Made with Bob
