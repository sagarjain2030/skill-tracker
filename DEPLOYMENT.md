# Deployment Guide

## Production Deployment on Render

The application is now configured to serve the React frontend from the root URL and API from `/api/*` routes.

### What happens on deployment:

1. **Build Process:**
   - Install Python dependencies: `pip install -r requirements.txt`
   - Install Node.js dependencies: `cd frontend && npm install`
   - Build React app: `npm run build` (creates `frontend/build` directory)

2. **Runtime:**
   - FastAPI serves the React app from root: `https://skill-tracker-p39k.onrender.com/`
   - API available at: `https://skill-tracker-p39k.onrender.com/api/skills/`
   - API docs at: `https://skill-tracker-p39k.onrender.com/docs`

### URLs after deployment:

- **`/`** → React Frontend (Skill Tracker UI)
- **`/api/skills/`** → Skills API endpoints
- **`/docs`** → API Documentation (Swagger UI)
- **`/health`** → Health check endpoint

### Local Development:

Run backend and frontend separately for development:

**Backend:**
```bash
.venv\Scripts\activate
uvicorn app.main:app --reload
# Runs on http://localhost:8000
```

**Frontend:**
```bash
cd frontend
npm start
# Runs on http://localhost:3000
# Proxies API calls to backend
```

### Changes Made:

1. **app/main.py:**
   - Added static file mounting for React build
   - Root route serves `index.html` if build exists, otherwise redirects to `/docs`
   - CORS configured for development and production

2. **render.yaml:**
   - Updated build command to include frontend build
   - Added NODE_VERSION environment variable

3. **.gitignore:**
   - Added `frontend/build/` and `frontend/node_modules/`

### Deploy to Render:

```bash
git add .
git commit -m "Configure frontend serving from backend"
git push
```

Render will automatically:
- Detect the changes
- Build both backend and frontend
- Deploy the full-stack application
- Serve everything from one URL
