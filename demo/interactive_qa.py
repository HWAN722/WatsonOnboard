"""
Demo script: Interactive Q&A with a codebase.

This script demonstrates the Q&A capabilities:
1. Load indexed codebase from vector store
2. Accept user questions
3. Retrieve relevant code chunks
4. Generate answers using Watsonx
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.watsonx.client import WatsonxClient
from src.qa.vector_store import VectorStore
from src.qa.retriever import Retriever
from src.config import settings


def main():
    """Run the interactive Q&A demo."""
    print(f"\n{'='*60}")
    print("WatsonOnboard Demo - Interactive Q&A")
    print(f"{'='*60}\n")
    
    # Initialize components
    print("Initializing Watsonx client and vector store...")
    watsonx_client = WatsonxClient(
        api_key=settings.WATSONX_API_KEY,
        project_id=settings.WATSONX_PROJECT_ID,
        url=settings.WATSONX_URL,
    )
    vector_store = VectorStore()
    
    # Check if vector store has data
    chunk_count = vector_store.collection.count()
    if chunk_count == 0:
        print("\n⚠️  No indexed codebase found!")
        print("Please run the analysis demo first:")
        print("  python demo/analyze_sample_repo.py")
        sys.exit(1)
    
    print(f"✓ Loaded vector store with {chunk_count} code chunks\n")
    
    # Initialize retriever
    retriever = Retriever(vector_store, watsonx_client)
    
    print("You can now ask questions about the codebase.")
    print("Type 'exit' or 'quit' to leave.\n")
    print(f"{'='*60}\n")
    
    # Interactive loop
    while True:
        try:
            question = input("❓ Your question: ").strip()
            
            if not question:
                continue
            
            if question.lower() in ["exit", "quit", "q"]:
                print("\n👋 Goodbye!")
                break
            
            print("\n🤔 Thinking...\n")
            
            # Get answer
            answer = retriever.answer_question(question, top_k=5)
            
            print(f"💡 Answer:\n{answer}\n")
            print(f"{'-'*60}\n")
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {str(e)}\n")


if __name__ == "__main__":
    main()

# Made with Bob
