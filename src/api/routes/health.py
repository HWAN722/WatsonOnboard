"""Health check endpoint."""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str
    watsonx: str


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.
    
    Returns the API status and Watsonx connectivity status.
    """
    # TODO: Add actual Watsonx connectivity check
    watsonx_status = "unknown"
    
    try:
        # This will be implemented when we have the Watsonx client
        # from src.watsonx.client import WatsonxClient
        # client = WatsonxClient()
        # client.ping()
        watsonx_status = "reachable"
    except Exception:
        watsonx_status = "unreachable"
    
    return HealthResponse(
        status="ok",
        watsonx=watsonx_status,
    )

# Made with Bob
