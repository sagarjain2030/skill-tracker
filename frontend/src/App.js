import React, { useState, useEffect } from 'react';
import skillService, { counterService } from './services/api';
import SkillTree from './components/SkillTree';
import AddSkillForm from './components/AddSkillForm';
import SkillSummary from './components/SkillSummary';
import ImportExport from './components/ImportExport';
import './App.css';

function App() {
  const [skills, setSkills] = useState([]);
  const [counters, setCounters] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedSkillId, setSelectedSkillId] = useState(null);
  const [showSummary, setShowSummary] = useState(false);

  // Load skills and counters on mount
  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [skillsData, countersData] = await Promise.all([
        skillService.getAllSkills(),
        counterService.getAllCounters()
      ]);
      setSkills(skillsData);
      setCounters(countersData);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load data');
      console.error('Error loading data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleAddRootSkill = async (name) => {
    try {
      await skillService.createRootSkill(name);
      await loadData();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create skill');
      throw err;
    }
  };

  const handleAddSubskill = async (parentId, name) => {
    try {
      await skillService.createSubskill(parentId, name);
      await loadData();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create subskill');
      throw err;
    }
  };

  const handleUpdateSkill = async (id, updates) => {
    try {
      await skillService.updateSkill(id, updates);
      await loadData();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update skill');
      throw err;
    }
  };

  const handleDeleteSkill = async (id) => {
    try {
      await skillService.deleteSkill(id);
      await loadData();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to delete skill');
      throw err;
    }
  };

  const handleClearAllData = async () => {
    const confirmed = window.confirm(
      '⚠️ WARNING: This will permanently delete ALL skills and counters. This action cannot be undone!\n\nAre you sure you want to continue?'
    );
    
    if (!confirmed) return;
    
    try {
      await counterService.clearAllData();
      await loadData();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to clear data');
      throw err;
    }
  };

  const handleViewSummary = (skillId) => {
    setSelectedSkillId(skillId);
    setShowSummary(true);
  };

  const handleCloseSummary = () => {
    setShowSummary(false);
    setSelectedSkillId(null);
  };

  // Build tree structure from flat list with counters
  const buildTree = (skills, counters) => {
    const skillMap = {};
    const roots = [];

    // Create a map of all skills with counters
    skills.forEach(skill => {
      skillMap[skill.id] = { 
        ...skill, 
        children: [],
        counters: counters.filter(c => c.skill_id === skill.id)
      };
    });

    // Build the tree
    skills.forEach(skill => {
      if (skill.parent_id === null) {
        roots.push(skillMap[skill.id]);
      } else if (skillMap[skill.parent_id]) {
        skillMap[skill.parent_id].children.push(skillMap[skill.id]);
      }
    });

    // Calculate accumulated counters for each node
    const calculateAccumulatedCounters = (node) => {
      // Start with direct counters
      const accumulated = {};
      
      node.counters.forEach(counter => {
        const key = `${counter.name}|${counter.unit || ''}`;
        if (!accumulated[key]) {
          accumulated[key] = {
            name: counter.name,
            unit: counter.unit,
            value: 0,
            target: 0,
            ids: []
          };
        }
        accumulated[key].value += counter.value;
        // Add target if it exists
        if (counter.target !== null && counter.target !== undefined) {
          accumulated[key].target += counter.target;
        }
        accumulated[key].ids.push(counter.id);
      });

      // Recursively add children's counters
      node.children.forEach(child => {
        const childAccumulated = calculateAccumulatedCounters(child);
        Object.entries(childAccumulated).forEach(([key, data]) => {
          if (!accumulated[key]) {
            accumulated[key] = {
              name: data.name,
              unit: data.unit,
              value: 0,
              target: 0,
              ids: []
            };
          }
          accumulated[key].value += data.value;
          // Sum up target values from all children
          if (data.target !== null && data.target !== undefined) {
            accumulated[key].target = (accumulated[key].target || 0) + data.target;
          }
          accumulated[key].ids.push(...data.ids);
        });
      });

      node.accumulatedCounters = Object.values(accumulated);
      return accumulated;
    };

    roots.forEach(root => calculateAccumulatedCounters(root));

    return roots;
  };

  const skillTree = buildTree(skills, counters);

  return (
    <div className="App">
      <header className="App-header">
        <h1>🎯 Skill Tracker</h1>
        <p>Hierarchical Skill Management System</p>
        <button 
          className="clear-data-btn"
          onClick={handleClearAllData}
          title="Delete all skills and counters"
        >
          🗑️ Clear All Data
        </button>
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
            <ImportExport onImport={loadData} />
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
                onRefresh={loadData}
                onViewSummary={handleViewSummary}
              />
            )}
          </div>
        </div>

        {showSummary && selectedSkillId && (
          <>
            <div 
              className="summary-overlay" 
              onClick={handleCloseSummary}
            />
            <SkillSummary 
              skillId={selectedSkillId} 
              onClose={handleCloseSummary}
            />
          </>
        )}
      </main>

      <footer className="App-footer">
        <p>Built with React & FastAPI | Milestone-1: Core Domain Skills</p>
      </footer>
    </div>
  );
}

export default App;
