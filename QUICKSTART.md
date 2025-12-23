# Quick Start Guide

## Running the Full Stack Application

### 1. Start the Backend

Open a terminal in the project root:

```bash
# Activate virtual environment
.\.venv\Scripts\activate

# Start FastAPI server
uvicorn app.main:app --reload
```

Backend will be available at:
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### 2. Start the Frontend

Open a **new terminal** in the project root:

```bash
# Navigate to frontend
cd frontend

# Install dependencies (first time only)
npm install

# Start React dev server
npm start
```

Frontend will automatically open at: http://localhost:3000

### 3. Using the Application

Once both servers are running:

1. **Open your browser** to http://localhost:3000
2. **Add a root skill** using the form on the left sidebar
3. **Add subskills** by clicking the `+` button on any skill
4. **Edit skill names** by clicking the pencil ✎ icon
5. **Delete skills** by clicking the × icon (will delete entire subtree)
6. **Expand/collapse** tree branches using the ▶ / ▼ buttons

### Features Available

✅ Create root skills  
✅ Create subskills (nested hierarchy)  
✅ Update skill names (inline editing)  
✅ Delete skills (cascading delete)  
✅ Expand/collapse tree visualization  
✅ Beautiful gradient UI  
✅ Real-time updates  

### Troubleshooting

**Port already in use:**
- Backend: Change port with `uvicorn app.main:app --reload --port 8001`
- Frontend: Will prompt to use different port

**CORS errors:**
- Ensure backend is running on port 8000
- Check CORS middleware is configured in `app/main.py`

**Module not found errors:**
- Backend: Activate venv and run `pip install -r requirements.txt`
- Frontend: Run `npm install` in frontend directory

### Development Tips

- Backend changes auto-reload with `--reload` flag
- Frontend changes auto-reload (hot module replacement)
- API documentation available at http://localhost:8000/docs
- All changes are in-memory (data resets on backend restart)

### What's Next?

As we progress through milestones, we'll add:
- Progress tracking UI
- Database persistence
- User authentication
- Analytics dashboard
- More...
