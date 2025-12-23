# Frontend

This directory contains the React-based UI for the Skill Tracker application.

## Setup

```bash
cd frontend
npm install
npm start
```

The app will run on http://localhost:3000 and proxy API requests to http://localhost:8000

## Structure

- `src/services/api.js` - API service for backend communication
- `src/components/` - React components
  - `SkillTree.js` - Main tree visualization
  - `SkillNode.js` - Individual skill node with CRUD operations
  - `AddSkillForm.js` - Form to add root skills
- `src/App.js` - Main application component
- `src/App.css` - Main application styles

## Features Implemented

- ✅ View hierarchical skill tree
- ✅ Create root skills
- ✅ Create subskills
- ✅ Update skill names (inline editing)
- ✅ Delete skills (cascading delete)
- ✅ Expand/collapse tree nodes
- ✅ Responsive design

## Future Enhancements (as we progress through milestones)

- Progress tracking visualization
- Skill assessments
- Learning resources
- User authentication
- Dashboard with analytics
