"""
CLI interface for WatsonOnboard using Typer.
Provides commands for analyzing repositories and querying codebases.
"""

import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt
from rich.table import Table
from rich.markdown import Markdown
from pathlib import Path

from src.config import settings
from src.report.orchestrator import AnalysisPipeline

app = typer.Typer(
    name="watson-onboard",
    help="Legacy Code Onboarding Assistant powered by IBM Watsonx",
    add_completion=False,
)
console = Console()


@app.command()
def analyze(
    repo_path: str = typer.Argument(..., help="Path to the repository to analyze"),
    output: Optional[str] = typer.Option(
        None, "--output", "-o", help="Output file path for the report"
    ),
    format: str = typer.Option(
        "markdown", "--format", "-f", help="Output format (markdown, json)"
    ),
    interactive: bool = typer.Option(
        False, "--interactive", "-i", help="Enable interactive Q&A after analysis"
    ),
) -> None:
    """
    Analyze a repository and generate an onboarding report.
    
    Example:
        watson-onboard analyze /path/to/repo --output report.md
    """
    console.print(f"[bold blue]Analyzing repository:[/bold blue] {repo_path}")
    
    repo_path_obj = Path(repo_path)
    if not repo_path_obj.exists():
        console.print(f"[bold red]Error:[/bold red] Repository path does not exist: {repo_path}")
        raise typer.Exit(code=1)
    
    try:
        with console.status("[bold green]Analyzing repository...[/bold green]"):
            # Run the analysis pipeline
            pipeline = AnalysisPipeline(repo_path_obj, use_llm=True, use_cache=True)
            
            # Set output path if provided
            output_path_obj = Path(output) if output else None
            report = pipeline.run(output_path=output_path_obj)
        
        # Save report
        if output:
            output_path = Path(output)
            output_path.write_text(report, encoding="utf-8")
            console.print(f"[bold green]✓[/bold green] Report saved to: {output}")
        else:
            console.print("\n[bold]Generated Report:[/bold]\n")
            console.print(Markdown(report))
        
        # Interactive Q&A mode
        if interactive:
            console.print("\n[bold blue]Entering interactive Q&A mode...[/bold blue]")
            console.print("Type 'exit' or 'quit' to leave.\n")
            
            retriever = Retriever(vector_store, watsonx_client)
            
            while True:
                question = Prompt.ask("[bold cyan]Ask a question about the codebase[/bold cyan]")
                
                if question.lower() in ["exit", "quit", "q"]:
                    console.print("[bold]Goodbye![/bold]")
                    break
                
                with console.status("[bold green]Thinking...[/bold green]"):
                    answer = retriever.answer_question(question, top_k=5)
                
                console.print(f"\n[bold green]Answer:[/bold green]\n{answer}\n")
        
    except Exception as e:
        console.print(f"[bold red]Error during analysis:[/bold red] {str(e)}")
        raise typer.Exit(code=1)


@app.command()
def ask(
    question: str = typer.Argument(..., help="Question to ask about the codebase"),
    repo_path: Optional[str] = typer.Option(
        None, "--repo", "-r", help="Path to the repository (if not already indexed)"
    ),
    top_k: int = typer.Option(
        5, "--top-k", "-k", help="Number of relevant code chunks to retrieve"
    ),
) -> None:
    """
    Ask a question about a previously analyzed codebase.
    
    Example:
        watson-onboard ask "How does authentication work?" --repo /path/to/repo
    """
    console.print(f"[bold blue]Question:[/bold blue] {question}\n")
    
    try:
        # Initialize components
        watsonx_client = WatsonxClient(
            api_key=settings.WATSONX_API_KEY,
            project_id=settings.WATSONX_PROJECT_ID,
            url=settings.WATSONX_URL,
        )
        vector_store = VectorStore()
        
        # If repo_path provided, need to index first
        if repo_path:
            console.print("[yellow]Repository not indexed. Please run 'analyze' command first.[/yellow]")
            raise typer.Exit(code=1)
        
        # Check if vector store has data
        if vector_store.collection.count() == 0:
            console.print("[yellow]No indexed codebase found. Please run 'analyze' command first.[/yellow]")
            raise typer.Exit(code=1)
        
        retriever = Retriever(vector_store, watsonx_client)
        
        with console.status("[bold green]Searching codebase and generating answer...[/bold green]"):
            answer = retriever.answer_question(question, top_k=top_k)
        
        console.print(f"[bold green]Answer:[/bold green]\n")
        console.print(Markdown(answer))
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        raise typer.Exit(code=1)


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query for semantic code search"),
    top_k: int = typer.Option(
        10, "--top-k", "-k", help="Number of results to return"
    ),
) -> None:
    """
    Perform semantic search on the indexed codebase.
    
    Example:
        watson-onboard search "database connection logic" --top-k 5
    """
    console.print(f"[bold blue]Searching for:[/bold blue] {query}\n")
    
    try:
        watsonx_client = WatsonxClient(
            api_key=settings.WATSONX_API_KEY,
            project_id=settings.WATSONX_PROJECT_ID,
            url=settings.WATSONX_URL,
        )
        vector_store = VectorStore()
        
        if vector_store.collection.count() == 0:
            console.print("[yellow]No indexed codebase found. Please run 'analyze' command first.[/yellow]")
            raise typer.Exit(code=1)
        
        embedder = Embedder(watsonx_client)
        
        with console.status("[bold green]Searching...[/bold green]"):
            query_embedding = embedder.embed(query)
            results = vector_store.search(query_embedding, top_k=top_k)
        
        # Display results in a table
        table = Table(title="Search Results", show_header=True, header_style="bold magenta")
        table.add_column("Rank", style="dim", width=6)
        table.add_column("File", style="cyan")
        table.add_column("Score", justify="right", style="green")
        table.add_column("Preview", style="white")
        
        for idx, result in enumerate(results, 1):
            chunk = result["chunk"]
            score = result["score"]
            preview = chunk.content[:100].replace("\n", " ") + "..."
            
            table.add_row(
                str(idx),
                chunk.file_path,
                f"{score:.3f}",
                preview,
            )
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        raise typer.Exit(code=1)


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", "--host", "-h", help="Host to bind to"),
    port: int = typer.Option(8000, "--port", "-p", help="Port to bind to"),
    reload: bool = typer.Option(False, "--reload", help="Enable auto-reload"),
) -> None:
    """
    Start the FastAPI server for the REST API.
    
    Example:
        watson-onboard serve --port 8000 --reload
    """
    console.print(f"[bold blue]Starting WatsonOnboard API server...[/bold blue]")
    console.print(f"Host: {host}")
    console.print(f"Port: {port}")
    console.print(f"Reload: {reload}\n")
    
    try:
        import uvicorn
        from src.api.main import app as fastapi_app
        
        uvicorn.run(
            "src.api.main:app",
            host=host,
            port=port,
            reload=reload,
        )
    except ImportError:
        console.print("[bold red]Error:[/bold red] uvicorn not installed. Run: pip install uvicorn")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[bold red]Error starting server:[/bold red] {str(e)}")
        raise typer.Exit(code=1)


@app.command()
def version() -> None:
    """Display version information."""
    console.print("[bold]WatsonOnboard[/bold] - Legacy Code Onboarding Assistant")
    console.print("Version: 0.1.0")
    console.print("Powered by IBM Watsonx")


def main() -> None:
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()

# Made with Bob
