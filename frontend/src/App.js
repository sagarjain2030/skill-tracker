import React, { useState, useEffect } from 'react';
import skillService from './services/api';
import SkillTree from './components/SkillTree';
import AddSkillForm from './components/AddSkillForm';
import './App.css';

function App() {
  const [skills, setSkills] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Load skills on mount
  useEffect(() => {
    loadSkills();
  }, []);

  const loadSkills = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await skillService.getAllSkills();
      setSkills(data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load skills');
      console.error('Error loading skills:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleAddRootSkill = async (name) => {
    try {
      await skillService.createRootSkill(name);
      await loadSkills();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create skill');
      throw err;
    }
  };

  const handleAddSubskill = async (parentId, name) => {
    try {
      await skillService.createSubskill(parentId, name);
      await loadSkills();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create subskill');
      throw err;
    }
  };

  const handleUpdateSkill = async (id, updates) => {
    try {
      await skillService.updateSkill(id, updates);
      await loadSkills();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update skill');
      throw err;
    }
  };

  const handleDeleteSkill = async (id) => {
    try {
      await skillService.deleteSkill(id);
      await loadSkills();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to delete skill');
      throw err;
    }
  };

  // Build tree structure from flat list
  const buildTree = (skills) => {
    const skillMap = {};
    const roots = [];

    // Create a map of all skills
    skills.forEach(skill => {
      skillMap[skill.id] = { ...skill, children: [] };
    });

    // Build the tree
    skills.forEach(skill => {
      if (skill.parent_id === null) {
        roots.push(skillMap[skill.id]);
      } else if (skillMap[skill.parent_id]) {
        skillMap[skill.parent_id].children.push(skillMap[skill.id]);
      }
    });

    return roots;
  };

  const skillTree = buildTree(skills);

  return (
    <div className="App">
      <header className="App-header">
        <h1>🎯 Skill Tracker</h1>
        <p>Hierarchical Skill Management System</p>
      </header>

      <main className="App-main">
        {error && (
          <div className="error-message">
            {error}
            <button onClick={() => setError(null)}>×</button>
          </div>
        )}

        <div className="content-container">
          <div className="sidebar">
            <AddSkillForm onAddSkill={handleAddRootSkill} />
          </div>

          <div className="main-content">
            {loading ? (
              <div className="loading">Loading skills...</div>
            ) : skillTree.length === 0 ? (
              <div className="empty-state">
                <h2>No skills yet</h2>
                <p>Create your first skill to get started!</p>
              </div>
            ) : (
              <SkillTree
                skills={skillTree}
                onAddSubskill={handleAddSubskill}
                onUpdateSkill={handleUpdateSkill}
                onDeleteSkill={handleDeleteSkill}
              />
            )}
          </div>
        </div>
      </main>

      <footer className="App-footer">
        <p>Built with React & FastAPI | Milestone-1: Core Domain Skills</p>
      </footer>
    </div>
  );
}

export default App;
