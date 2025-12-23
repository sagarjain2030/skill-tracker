# app/main.py
from fastapi import FastAPI, Response
from fastapi.responses import RedirectResponse
import os

app = FastAPI(
    title="Skill Tracker API",
    description="""
    A hierarchical skill tracking system with progress monitoring, streaks, and analytics.
    
    ## Features
    
    * **Skill Tree Management** - Create and manage hierarchical skill trees
    * **Progress Tracking** - Log daily progress for skills
    * **Streak Calculation** - Track current and longest streaks
    * **Metrics & Analytics** - View skill-level and tree-level insights
    
    ## Coming Soon
    
    * Skill CRUD operations
    * Counter system
    * Progress logging
    * Tree traversal and aggregation
    """,
    version="0.1.0",
    contact={
        "name": "Skill Tracker",
        "url": "https://github.com/sagarjain2030/skill-tracker",
    },
    license_info={
        "name": "MIT",
    },
)

@app.get("/favicon.ico")
def favicon():
    return Response(status_code=204)

@app.get("/", include_in_schema=False)
def root():
    """Redirect root to API documentation."""
    return RedirectResponse(url="/docs")


@app.get("/health", tags=["System"])
def health_check():
    """Health check endpoint."""
    return {"status": "ok"}

@app.api_route("/version", methods=["GET", "HEAD"], tags=["System"])
def version():
    """Get deployment version and commit information."""
    return {
        "commit": os.getenv("RENDER_GIT_COMMIT", "unknown"),
        "service": os.getenv("RENDER_SERVICE_NAME", "unknown"),
        "version": app.version,
    }