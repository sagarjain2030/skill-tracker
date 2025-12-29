import React, { useState } from 'react';
import { counterService } from '../services/api';
import './SkillNode.css';

function SkillNode({ 
  skill, 
  level, 
  isExpanded, 
  expandedNodes,
  onToggle, 
  onAddSubskill, 
  onUpdateSkill, 
  onDeleteSkill,
  onRefresh,
  onViewSummary
}) {
  const [isEditing, setIsEditing] = useState(false);
  const [editName, setEditName] = useState(skill.name);
  const [showAddChild, setShowAddChild] = useState(false);
  const [childName, setChildName] = useState('');
  const [showAddCounter, setShowAddCounter] = useState(false);
  const [counterForm, setCounterForm] = useState({ name: '', unit: '', value: 0, target: '' });
  const [showCounters, setShowCounters] = useState(false);
  const [loading, setLoading] = useState(false);

  const hasChildren = skill.children && skill.children.length > 0;

  const handleUpdate = async () => {
    if (!editName.trim() || editName === skill.name) {
      setIsEditing(false);
      return;
    }

    setLoading(true);
    try {
      await onUpdateSkill(skill.id, { name: editName.trim() });
      setIsEditing(false);
    } catch (err) {
      console.error('Error updating skill:', err);
      setEditName(skill.name);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    const confirmMsg = hasChildren
      ? `Delete "${skill.name}" and all its children?`
      : `Delete "${skill.name}"?`;
    
    if (!window.confirm(confirmMsg)) return;

    setLoading(true);
    try {
      await onDeleteSkill(skill.id);
    } catch (err) {
      console.error('Error deleting skill:', err);
      setLoading(false);
    }
  };

  const handleAddChild = async (e) => {
    e.preventDefault();
    if (!childName.trim()) return;

    setLoading(true);
    try {
      await onAddSubskill(skill.id, childName.trim());
      setChildName('');
      setShowAddChild(false);
      if (!isExpanded) {
        onToggle(skill.id);
      }
    } catch (err) {
      console.error('Error adding subskill:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleAddCounter = async (e) => {
    e.preventDefault();
    if (!counterForm.name.trim()) return;

    setLoading(true);
    try {
      await counterService.createCounter(skill.id, {
        name: counterForm.name.trim(),
        unit: counterForm.unit.trim() || null,
        value: parseFloat(counterForm.value) || 0,
        target: counterForm.target ? parseFloat(counterForm.target) : null
      });
      setCounterForm({ name: '', unit: '', value: 0, target: '' });
      setShowAddCounter(false);
      setShowCounters(true);
      await onRefresh();
    } catch (err) {
      console.error('Error adding counter:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleIncrementCounter = async (counterId, amount = 1) => {
    setLoading(true);
    try {
      await counterService.incrementCounter(counterId, amount);
      await onRefresh();
    } catch (err) {
      console.error('Error incrementing counter:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteCounter = async (counterId) => {
    if (!window.confirm('Delete this counter?')) return;

    setLoading(true);
    try {
      await counterService.deleteCounter(counterId);
      await onRefresh();
    } catch (err) {
      console.error('Error deleting counter:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="skill-node" style={{ '--level': level }}>
      <div className="node-header">
        <div className="node-left">
          {hasChildren && (
            <button
              className="expand-btn"
              onClick={() => onToggle(skill.id)}
              disabled={loading}
            >
              {isExpanded ? '▼' : '▶'}
            </button>
          )}
          {!hasChildren && <span className="expand-spacer"></span>}

          {isEditing ? (
            <input
              type="text"
              value={editName}
              onChange={(e) => setEditName(e.target.value)}
              onBlur={handleUpdate}
              onKeyPress={(e) => e.key === 'Enter' && handleUpdate()}
              disabled={loading}
              autoFocus
              className="edit-input"
              maxLength={255}
            />
          ) : (
            <span className="skill-name" title={skill.name}>
              {skill.name}
            </span>
          )}
        </div>

        <div className="node-actions">
          <button
            className="action-btn summary-btn"
            onClick={() => onViewSummary && onViewSummary(skill.id)}
            disabled={loading}
            title="View skill summary"
          >
            📋
          </button>
          <button
            className="action-btn counter-btn"
            onClick={() => setShowCounters(!showCounters)}
            disabled={loading}
            title={`View counters (${(skill.counters?.length || 0)} direct)`}
          >
            📊 {(skill.counters?.length || 0) > 0 && <span className="counter-badge">{skill.counters.length}</span>}
          </button>
          <button
            className="action-btn add-btn"
            onClick={() => setShowAddChild(!showAddChild)}
            disabled={loading}
            title="Add subskill"
          >
            +
          </button>
          <button
            className="action-btn edit-btn"
            onClick={() => setIsEditing(!isEditing)}
            disabled={loading}
            title="Edit skill"
          >
            ✎
          </button>
          <button
            className="action-btn delete-btn"
            onClick={handleDelete}
            disabled={loading}
            title="Delete skill"
          >
            ×
          </button>
        </div>
      </div>

      {showAddChild && (
        <div className="add-child-form">
          <form onSubmit={handleAddChild}>
            <input
              type="text"
              value={childName}
              onChange={(e) => setChildName(e.target.value)}
              placeholder="New subskill name..."
              disabled={loading}
              maxLength={255}
            />
            <button type="submit" disabled={!childName.trim() || loading}>
              Add
            </button>
            <button
              type="button"
              onClick={() => {
                setShowAddChild(false);
                setChildName('');
              }}
              disabled={loading}
            >
              Cancel
            </button>
          </form>
        </div>
      )}

      {showCounters && (
        <div className="counters-section">
          <div className="counters-header">
            <h4>Counters for {skill.name}</h4>
            <button
              className="add-counter-btn"
              onClick={() => setShowAddCounter(!showAddCounter)}
              disabled={loading}
            >
              + Add Counter
            </button>
          </div>

          {showAddCounter && (
            <div className="add-counter-form">
              <form onSubmit={handleAddCounter}>
                <input
                  type="text"
                  value={counterForm.name}
                  onChange={(e) => setCounterForm({...counterForm, name: e.target.value})}
                  placeholder="Counter name (e.g., Hours)"
                  disabled={loading}
                  maxLength={255}
                />
                <input
                  type="text"
                  value={counterForm.unit}
                  onChange={(e) => setCounterForm({...counterForm, unit: e.target.value})}
                  placeholder="Unit (optional)"
                  disabled={loading}
                  maxLength={50}
                />
                <input
                  type="number"
                  step="0.1"
                  value={counterForm.value}
                  onChange={(e) => setCounterForm({...counterForm, value: e.target.value})}
                  placeholder="Initial value"
                  disabled={loading}
                />
                <input
                  type="number"
                  step="0.1"
                  value={counterForm.target}
                  onChange={(e) => setCounterForm({...counterForm, target: e.target.value})}
                  placeholder="Target (optional)"
                  disabled={loading}
                />
                <button type="submit" disabled={!counterForm.name.trim() || loading}>
                  Add
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setShowAddCounter(false);
                    setCounterForm({ name: '', unit: '', value: 0, target: '' });
                  }}
                  disabled={loading}
                >
                  Cancel
                </button>
              </form>
            </div>
          )}

          {/* Show accumulated counters (includes own + children) */}
          {skill.accumulatedCounters && skill.accumulatedCounters.length > 0 && (
            <div className="counters-list">
              <h5>📈 Total (this skill + all children):</h5>
              {skill.accumulatedCounters.map((counter, idx) => (
                <div key={idx} className="accumulated-counter-item">
                  <div className="counter-info">
                    <span className="counter-name">{counter.name}</span>
                    <span className="counter-value accumulated">
                      {counter.value.toFixed(1)} {counter.unit || ''}
                      {counter.target && ` / ${counter.target}`}
                    </span>
                    {counter.target && (
                      <div className="counter-progress">
                        <div 
                          className="progress-bar accumulated" 
                          style={{width: `${Math.min((counter.value / counter.target) * 100, 100)}%`}}
                        />
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Show message if no counters at all */}
          {(!skill.accumulatedCounters || skill.accumulatedCounters.length === 0) && 
           (!skill.counters || skill.counters.length === 0) && (
            <p style={{color: '#999', padding: '1rem', textAlign: 'center'}}>
              No counters yet. Click "+ Add Counter" to create one.
            </p>
          )}

          {/* Show direct counters (only this skill) */}
          {skill.counters && skill.counters.length > 0 && (
            <div className="counters-list" style={{marginTop: '1rem'}}>
              <h5>🎯 Direct (this skill only):</h5>
              {skill.counters.map(counter => (
                <div key={counter.id} className="counter-item">
                  <div className="counter-info">
                    <span className="counter-name">{counter.name}</span>
                    <span className="counter-value">
                      {counter.value.toFixed(1)} {counter.unit || ''}
                      {counter.target && ` / ${counter.target}`}
                    </span>
                    {counter.target && (
                      <div className="counter-progress">
                        <div 
                          className="progress-bar" 
                          style={{width: `${Math.min((counter.value / counter.target) * 100, 100)}%`}}
                        />
                      </div>
                    )}
                  </div>
                  <div className="counter-actions">
                    <button
                      onClick={() => handleIncrementCounter(counter.id, 1)}
                      disabled={loading}
                      title="Increment by 1"
                    >
                      +1
                    </button>
                    <button
                      onClick={() => handleIncrementCounter(counter.id, 0.5)}
                      disabled={loading}
                      title="Increment by 0.5"
                    >
                      +0.5
                    </button>
                    <button
                      onClick={() => handleDeleteCounter(counter.id)}
                      disabled={loading}
                      className="delete-counter-btn"
                      title="Delete counter"
                    >
                      ×
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {isExpanded && hasChildren && (
        <div className="node-children">
          {skill.children.map(child => (
            <SkillNode
              key={child.id}
              skill={child}
              onViewSummary={onViewSummary}
              level={level + 1}
              isExpanded={expandedNodes.has(child.id)}
              expandedNodes={expandedNodes}
              onToggle={onToggle}
              onAddSubskill={onAddSubskill}
              onUpdateSkill={onUpdateSkill}
              onDeleteSkill={onDeleteSkill}
              onRefresh={onRefresh}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export default SkillNode;
