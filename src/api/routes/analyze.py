"""API routes for repository analysis."""

import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict

from fastapi import APIRouter, BackgroundTasks, HTTPException

from src.api.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    JobStatus,
    JobStatusResponse,
)
from src.report.orchestrator import analyze_repository

router = APIRouter()

# In-memory job store (use Redis/database in production)
jobs: Dict[str, dict] = {}


def run_analysis_job(job_id: str, request: AnalyzeRequest) -> None:
    """
    Run analysis job in background.
    
    Args:
        job_id: Job identifier
        request: Analysis request
    """
    try:
        # Update job status
        jobs[job_id]["status"] = JobStatus.RUNNING
        jobs[job_id]["progress"] = 10
        jobs[job_id]["message"] = "Starting analysis..."
        jobs[job_id]["updated_at"] = datetime.utcnow()

        # Run analysis
        repo_path = Path(request.repo_path)
        
        if not repo_path.exists():
            raise ValueError(f"Repository path does not exist: {request.repo_path}")

        # Update progress
        jobs[job_id]["progress"] = 30
        jobs[job_id]["message"] = "Scanning repository..."
        jobs[job_id]["updated_at"] = datetime.utcnow()

        # Generate output path
        output_path = repo_path / "ONBOARDING.md"

        # Run analysis
        report = analyze_repository(
            repo_path=repo_path,
            output_path=output_path,
            use_llm=request.use_llm,
            use_cache=request.use_cache,
        )

        # Update job as completed
        jobs[job_id]["status"] = JobStatus.COMPLETED
        jobs[job_id]["progress"] = 100
        jobs[job_id]["message"] = "Analysis completed successfully"
        jobs[job_id]["completed_at"] = datetime.utcnow()
        jobs[job_id]["updated_at"] = datetime.utcnow()
        jobs[job_id]["report_url"] = f"/api/reports/{job_id}"
        jobs[job_id]["report_content"] = report

    except Exception as e:
        # Update job as failed
        jobs[job_id]["status"] = JobStatus.FAILED
        jobs[job_id]["message"] = "Analysis failed"
        jobs[job_id]["error"] = str(e)
        jobs[job_id]["updated_at"] = datetime.utcnow()


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(
    request: AnalyzeRequest,
    background_tasks: BackgroundTasks,
) -> AnalyzeResponse:
    """
    Start repository analysis job.
    
    Args:
        request: Analysis request
        background_tasks: FastAPI background tasks
        
    Returns:
        Analysis response with job ID
    """
    # Generate job ID
    job_id = str(uuid.uuid4())

    # Create job entry
    now = datetime.utcnow()
    jobs[job_id] = {
        "job_id": job_id,
        "status": JobStatus.PENDING,
        "progress": 0,
        "message": "Job queued",
        "created_at": now,
        "updated_at": now,
        "completed_at": None,
        "report_url": None,
        "error": None,
        "request": request.model_dump(),
    }

    # Add background task
    background_tasks.add_task(run_analysis_job, job_id, request)

    return AnalyzeResponse(
        job_id=job_id,
        status=JobStatus.PENDING,
        message="Analysis job started",
        created_at=now,
    )


@router.get("/analyze/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str) -> JobStatusResponse:
    """
    Get status of an analysis job.
    
    Args:
        job_id: Job identifier
        
    Returns:
        Job status response
        
    Raises:
        HTTPException: If job not found
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs[job_id]

    return JobStatusResponse(
        job_id=job["job_id"],
        status=job["status"],
        progress=job["progress"],
        message=job["message"],
        created_at=job["created_at"],
        updated_at=job["updated_at"],
        completed_at=job.get("completed_at"),
        report_url=job.get("report_url"),
        error=job.get("error"),
    )


@router.get("/reports/{job_id}")
async def get_report(job_id: str) -> dict:
    """
    Get the generated report for a completed job.
    
    Args:
        job_id: Job identifier
        
    Returns:
        Report content
        
    Raises:
        HTTPException: If job not found or not completed
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs[job_id]

    if job["status"] != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Job not completed. Current status: {job['status']}",
        )

    return {
        "job_id": job_id,
        "report": job.get("report_content", ""),
        "created_at": job["created_at"],
        "completed_at": job["completed_at"],
    }


@router.delete("/analyze/{job_id}")
async def delete_job(job_id: str) -> dict:
    """
    Delete a job and its results.
    
    Args:
        job_id: Job identifier
        
    Returns:
        Deletion confirmation
        
    Raises:
        HTTPException: If job not found
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    del jobs[job_id]

    return {
        "message": "Job deleted successfully",
        "job_id": job_id,
    }


@router.get("/jobs")
async def list_jobs() -> dict:
    """
    List all analysis jobs.
    
    Returns:
        List of jobs with their status
    """
    job_list = []

    for job_id, job in jobs.items():
        job_list.append({
            "job_id": job_id,
            "status": job["status"],
            "progress": job["progress"],
            "created_at": job["created_at"],
            "updated_at": job["updated_at"],
        })

    return {
        "total": len(job_list),
        "jobs": job_list,
    }

# Made with Bob
