# app/main.py
from fastapi import FastAPI, Response
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
import os
from app.routers import skills

app = FastAPI(
    title="Skill Tracker API",
    description="""
    A hierarchical skill tracking system with progress monitoring, streaks, and analytics.
    
    ## Features
    
    * **Skill Tree Management** - Create and manage hierarchical skill trees
    * **Progress Tracking** - Log daily progress for skills
    * **Streak Calculation** - Track current and longest streaks
    * **Metrics & Analytics** - View skill-level and tree-level insights
    
    ## API Endpoints
    
    ### Skills
    * `POST /skills` - Create a root skill
    * `GET /skills` - List all skills
    * `GET /skills/{id}` - Get a skill by ID
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

# Configure CORS
allowed_origins = [
    "http://localhost:3000",  # React dev server
    "https://skill-tracker-p39k.onrender.com",  # Production frontend (if deployed separately)
]

# Allow all origins in development, specific origins in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if os.getenv("ENVIRONMENT") == "production" else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(skills.router, prefix="/api")

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