# app/main.py
from fastapi import FastAPI, Response, status
from fastapi.responses import RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os
from pathlib import Path
from app.routers import skills, counters
from app.storage_db import clear_all_data
from app.database import init_db

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

# Initialize database tables
init_db()

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
app.include_router(counters.router, prefix="/api")

# Mount static files for React frontend (if build directory exists)
frontend_build_path = Path(__file__).parent.parent / "frontend" / "build"
print(f"Looking for frontend build at: {frontend_build_path}")
print(f"Build directory exists: {frontend_build_path.exists()}")
if frontend_build_path.exists():
    print(f"Mounting static files from: {frontend_build_path / 'static'}")
    app.mount("/static", StaticFiles(directory=str(frontend_build_path / "static")), name="static")

@app.get("/favicon.ico")
def favicon():
    return Response(status_code=204)

@app.get("/", include_in_schema=False)
def root():
    """Serve React frontend or redirect to API documentation."""
    print(f"Root route called. Frontend build exists: {frontend_build_path.exists()}")
    if frontend_build_path.exists():
        print(f"Serving frontend from: {frontend_build_path / 'index.html'}")
        return FileResponse(str(frontend_build_path / "index.html"))
    print("Frontend build not found, redirecting to /docs")
    return RedirectResponse(url="/docs")


@app.get("/health", tags=["System"])
def health_check():
    """Health check endpoint."""
    return {"status": "ok"}

@app.get("/debug/storage", tags=["System"])
def debug_storage_info():
    """Debug endpoint to check storage paths and disk status."""
    import os
    from pathlib import Path
    
    data_dir = Path("data")
    skills_file = data_dir / "skills.json"
    counters_file = data_dir / "counters.json"
    
    return {
        "data_directory": str(data_dir.absolute()),
        "data_dir_exists": data_dir.exists(),
        "skills_file_exists": skills_file.exists(),
        "counters_file_exists": counters_file.exists(),
        "current_working_dir": os.getcwd(),
        "render_disk_mounted": os.path.exists("/opt/render/project/src/data"),
        "disk_contents": list(data_dir.iterdir()) if data_dir.exists() else []
    }

@app.api_route("/version", methods=["GET", "HEAD"], tags=["System"])
def version():
    """Get deployment version and commit information."""
    return {
        "commit": os.getenv("RENDER_GIT_COMMIT", "unknown"),
        "service": os.getenv("RENDER_SERVICE_NAME", "unknown"),
        "version": app.version,
    }

@app.delete("/api/data", status_code=status.HTTP_204_NO_CONTENT, tags=["System"])
def clear_all_app_data():
    """
    Delete all persisted data (skills and counters).
    
    ⚠️ WARNING: This permanently deletes all data and cannot be undone.
    
    Use this to reset your application to a clean state.
    """
    # Clear in-memory storage
    skills.skills_db.clear()
    counters.counters_db.clear()
    
    # Reset ID counters
    skills.next_skill_id = 1
    counters.next_counter_id = 1
    
    # Clear persistent files
    clear_all_data()
    
    return None