"""Prompt templates for Watsonx LLM interactions."""

from jinja2 import Template

# Module Summary Prompt
MODULE_SUMMARY_PROMPT = Template("""
You are a code documentation expert. Analyze the following code module and provide a concise summary.

File: {{ file_path }}
Language: {{ language }}
Lines of Code: {{ loc }}

Code:
```{{ language }}
{{ code }}
```

Provide a summary that includes:
1. Purpose: What does this module do?
2. Key Components: Main classes, functions, or exports
3. Dependencies: What does it depend on?
4. Usage: How is it typically used?

Keep the summary concise (3-5 sentences) and focus on the most important aspects.

Summary:
""".strip())


# Project TL;DR Prompt
PROJECT_TLDR_PROMPT = Template("""
You are a software architect analyzing a codebase. Based on the following information, provide a high-level overview.

Project Statistics:
- Total Files: {{ total_files }}
- Total Lines of Code: {{ total_loc }}
- Languages: {{ languages }}

Core Modules (most imported):
{% for module in core_modules %}
- {{ module.path }} (imported by {{ module.in_degree }} files)
{% endfor %}

Entry Points:
{% for entry in entry_points %}
- {{ entry.path }}
{% endfor %}

Provide a TL;DR (2-3 paragraphs) that explains:
1. What this project does
2. Its architecture and organization
3. Key technologies and patterns used

TL;DR:
""".strip())


# Reading List Prompt
READING_LIST_PROMPT = Template("""
You are helping a new developer understand a codebase. Based on the dependency analysis, suggest a reading order.

Core Modules:
{% for module in core_modules %}
- {{ module.path }}: {{ module.description }}
{% endfor %}

Entry Points:
{% for entry in entry_points %}
- {{ entry.path }}
{% endfor %}

Create a recommended reading list with:
1. Order to read files (start with foundational, then build up)
2. Brief reason for each file's placement
3. Estimated time to understand each file

Reading List:
""".strip())


# Q&A Answer Prompt
QA_ANSWER_PROMPT = Template("""
You are a helpful code assistant. Answer the following question about the codebase using the provided context.

Question: {{ question }}

Relevant Code Context:
{% for chunk in context_chunks %}
---
File: {{ chunk.file_path }}
Lines: {{ chunk.line_start }}-{{ chunk.line_end }}

```{{ chunk.language }}
{{ chunk.content }}
```
{% endfor %}

Instructions:
1. Answer the question directly and concisely
2. Reference specific files and line numbers when relevant
3. If the context doesn't contain enough information, say so
4. Provide code examples if helpful

Answer:
""".strip())


# Glossary Prompt
GLOSSARY_PROMPT = Template("""
You are creating a glossary for a codebase. Based on the following code elements, define key terms.

Classes:
{% for cls in classes %}
- {{ cls.name }}: {{ cls.docstring or "No description" }}
{% endfor %}

Functions:
{% for func in functions %}
- {{ func.name }}: {{ func.docstring or "No description" }}
{% endfor %}

Create a glossary with:
1. Term name
2. Brief definition (1-2 sentences)
3. Where it's used

Format as a markdown list.

Glossary:
""".strip())


# Architecture Explanation Prompt
ARCHITECTURE_PROMPT = Template("""
You are a software architect. Explain the architecture of this codebase based on the dependency graph.

Modules by Layer:
{% for layer, modules in layers.items() %}
{{ layer }}:
{% for module in modules %}
  - {{ module }}
{% endfor %}
{% endfor %}

Dependencies:
{% for dep in dependencies %}
- {{ dep.source }} → {{ dep.target }}
{% endfor %}

Explain:
1. The overall architecture pattern (e.g., layered, microservices, MVC)
2. How data flows through the system
3. Key design decisions evident from the structure

Architecture Overview:
""".strip())


# Code Quality Assessment Prompt
CODE_QUALITY_PROMPT = Template("""
You are a code reviewer. Assess the quality of this codebase based on the metrics.

Metrics:
- Total Files: {{ total_files }}
- Average LOC per file: {{ avg_loc }}
- Files with no docstrings: {{ no_docstring_count }}
- Circular dependencies: {{ circular_deps }}
- Isolated files: {{ isolated_files }}

Dependency Analysis:
- Most imported file: {{ most_imported.path }} ({{ most_imported.in_degree }} imports)
- Largest file: {{ largest_file.path }} ({{ largest_file.loc }} LOC)

Provide:
1. Overall code quality assessment (1-5 stars)
2. Strengths
3. Areas for improvement
4. Specific recommendations

Assessment:
""".strip())


# Function to render a template
def render_prompt(template: Template, **kwargs) -> str:
    """
    Render a prompt template with the given variables.
    
    Args:
        template: Jinja2 template
        **kwargs: Template variables
        
    Returns:
        Rendered prompt string
    """
    return template.render(**kwargs)


# Convenience functions for each prompt type
def create_module_summary_prompt(file_path: str, language: str, loc: int, code: str) -> str:
    """Create a module summary prompt."""
    return render_prompt(
        MODULE_SUMMARY_PROMPT,
        file_path=file_path,
        language=language,
        loc=loc,
        code=code,
    )


def create_project_tldr_prompt(
    total_files: int,
    total_loc: int,
    languages: dict,
    core_modules: list,
    entry_points: list,
) -> str:
    """Create a project TL;DR prompt."""
    return render_prompt(
        PROJECT_TLDR_PROMPT,
        total_files=total_files,
        total_loc=total_loc,
        languages=languages,
        core_modules=core_modules,
        entry_points=entry_points,
    )


def create_qa_answer_prompt(question: str, context_chunks: list) -> str:
    """Create a Q&A answer prompt."""
    return render_prompt(
        QA_ANSWER_PROMPT,
        question=question,
        context_chunks=context_chunks,
    )


def create_glossary_prompt(classes: list, functions: list) -> str:
    """Create a glossary prompt."""
    return render_prompt(
        GLOSSARY_PROMPT,
        classes=classes,
        functions=functions,
    )

# Made with Bob
