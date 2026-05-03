"""
Demo script: Test the REST API endpoints.

This script demonstrates API usage:
1. Start analysis job
2. Check job status
3. Query the codebase
4. Perform semantic search
"""

import sys
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx


def main():
    """Run the API demo."""
    base_url = "http://localhost:8000"
    
    print(f"\n{'='*60}")
    print("WatsonOnboard Demo - REST API")
    print(f"{'='*60}\n")
    
    print("⚠️  Make sure the API server is running:")
    print("  watson-onboard serve --port 8000\n")
    
    input("Press Enter when the server is ready...")
    
    # Test health endpoint
    print("\n1. Testing health endpoint...")
    try:
        response = httpx.get(f"{base_url}/health")
        response.raise_for_status()
        print(f"   ✓ Server is healthy: {response.json()}")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        print("   Make sure the server is running!")
        sys.exit(1)
    
    # Start analysis job
    print("\n2. Starting repository analysis...")
    repo_path = input("   Enter repository path: ").strip()
    
    try:
        response = httpx.post(
            f"{base_url}/api/analyze",
            json={"repo_path": repo_path},
            timeout=30.0,
        )
        response.raise_for_status()
        job_data = response.json()
        job_id = job_data["job_id"]
        print(f"   ✓ Analysis started. Job ID: {job_id}")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        sys.exit(1)
    
    # Poll job status
    print("\n3. Monitoring job progress...")
    max_attempts = 60
    attempt = 0
    
    while attempt < max_attempts:
        try:
            response = httpx.get(f"{base_url}/api/analyze/{job_id}")
            response.raise_for_status()
            status_data = response.json()
            status = status_data["status"]
            
            print(f"   Status: {status}", end="\r")
            
            if status == "COMPLETED":
                print(f"\n   ✓ Analysis completed!")
                break
            elif status == "FAILED":
                print(f"\n   ❌ Analysis failed: {status_data.get('error', 'Unknown error')}")
                sys.exit(1)
            
            time.sleep(2)
            attempt += 1
            
        except Exception as e:
            print(f"\n   ❌ Error: {str(e)}")
            sys.exit(1)
    
    if attempt >= max_attempts:
        print("\n   ⚠️  Job is taking too long. Check status manually.")
        sys.exit(1)
    
    # Download report
    print("\n4. Downloading report...")
    try:
        response = httpx.get(f"{base_url}/api/reports/{job_id}")
        response.raise_for_status()
        report = response.text
        
        output_file = "api_demo_report.md"
        Path(output_file).write_text(report, encoding="utf-8")
        print(f"   ✓ Report saved to: {output_file}")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    # Test query endpoint
    print("\n5. Testing Q&A endpoint...")
    question = input("   Enter a question about the codebase: ").strip()
    
    if question:
        try:
            response = httpx.post(
                f"{base_url}/api/query",
                json={"question": question, "top_k": 5},
                timeout=30.0,
            )
            response.raise_for_status()
            query_data = response.json()
            
            print(f"\n   💡 Answer:\n   {query_data['answer']}\n")
            print(f"   📚 Sources used: {len(query_data['sources'])}")
            
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
    
    # Test search endpoint
    print("\n6. Testing semantic search...")
    search_query = input("   Enter search query: ").strip()
    
    if search_query:
        try:
            response = httpx.post(
                f"{base_url}/api/search",
                json={"query": search_query, "top_k": 5},
                timeout=30.0,
            )
            response.raise_for_status()
            search_data = response.json()
            
            print(f"\n   🔍 Found {len(search_data['results'])} results:")
            for idx, result in enumerate(search_data['results'][:3], 1):
                print(f"   {idx}. {result['file_path']} (score: {result['score']:.3f})")
            
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
    
    # List all jobs
    print("\n7. Listing all jobs...")
    try:
        response = httpx.get(f"{base_url}/api/jobs")
        response.raise_for_status()
        jobs_data = response.json()
        
        print(f"   Total jobs: {len(jobs_data['jobs'])}")
        for job in jobs_data['jobs'][:5]:
            print(f"   - {job['job_id']}: {job['status']}")
        
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    print(f"\n{'='*60}")
    print("API Demo Complete!")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()

# Made with Bob
