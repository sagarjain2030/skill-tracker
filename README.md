# Skill Tracker - Full Stack Application

A hierarchical skill tracking system with progress monitoring, streaks, and analytics.

## Architecture

- **Backend**: FastAPI (Python)
- **Frontend**: React (JavaScript)
- **Database**: In-memory (to be replaced with SQLAlchemy + PostgreSQL in Milestone-3)

## Getting Started

### Backend Setup

```bash
# Clone the repository
git clone https://github.com/sagarjain2030/skill-tracker.git
cd skill-tracker

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # On Windows
# source .venv/bin/activate  # On Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Run backend
uvicorn app.main:app --reload
```

Backend runs on: http://localhost:8000  
API docs: http://localhost:8000/docs

### Frontend Setup

```bash
# From project root
cd frontend

# Install dependencies
npm install

# Run development server
npm start
```

Frontend runs on: http://localhost:3000

## Current Implementation Status

### ✅ Milestone-1: Core Domain - Skills

#### Completed Stories:
- **Story-1.1.1** ✅ Define Skill as hierarchical entity
- **Story-1.1.2** ✅ Prevent cyclic dependencies
- **Story-1.2.1** ✅ Create root skill
- **Story-1.2.2** ✅ Create subskill
- **Story-1.2.3** ✅ Update skill metadata
- **Story-1.2.4** ✅ Delete skill subtree

#### API Endpoints:
- `POST /api/skills/` - Create root skill
- `POST /api/skills/{parent_id}/children` - Create subskill
- `GET /api/skills/` - List all skills
- `GET /api/skills/{id}` - Get skill by ID
- `PATCH /api/skills/{id}` - Update skill (name, parent_id)
- `DELETE /api/skills/{id}` - Delete skill and entire subtree

#### Frontend Features:
- ✅ View hierarchical skill tree
- ✅ Create root skills
- ✅ Create subskills (inline)
- ✅ Update skill names (inline editing)
- ✅ Delete skills with cascading delete
- ✅ Expand/collapse tree nodes
- ✅ Beautiful gradient UI

### 🚧 Upcoming Milestones

- **Milestone-2**: Progress Tracking - Track daily progress, streaks, and metrics
- **Milestone-3**: Database Layer - SQLAlchemy + PostgreSQL integration
- **Milestone-4**: Metrics & Analytics - Insights and visualizations

## Running Tests

```bash
pytest tests/ -v
```

All 93 tests passing ✅

## Development

The frontend will be progressively enhanced as we complete more stories and milestones.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License.
