"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.routes import analyze, health, query
from src.config import settings

# Create FastAPI app
app = FastAPI(
    title="WatsonOnboard API",
    description="Legacy Code Onboarding Assistant powered by IBM Watsonx",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc),
        },
    )


# Include routers
app.include_router(health.router, tags=["health"])
app.include_router(analyze.router, prefix="/api", tags=["analyze"])
app.include_router(query.router, prefix="/api", tags=["query"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "WatsonOnboard API",
        "version": "0.1.0",
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
    )

# Made with Bob
