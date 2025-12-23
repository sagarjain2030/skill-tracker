import React, { useState } from 'react';
import './SkillNode.css';

function SkillNode({ 
  skill, 
  level, 
  isExpanded, 
  onToggle, 
  onAddSubskill, 
  onUpdateSkill, 
  onDeleteSkill 
}) {
  const [isEditing, setIsEditing] = useState(false);
  const [editName, setEditName] = useState(skill.name);
  const [showAddChild, setShowAddChild] = useState(false);
  const [childName, setChildName] = useState('');
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

      {isExpanded && hasChildren && (
        <div className="node-children">
          {skill.children.map(child => (
            <SkillNode
              key={child.id}
              skill={child}
              level={level + 1}
              isExpanded={false}
              onToggle={onToggle}
              onAddSubskill={onAddSubskill}
              onUpdateSkill={onUpdateSkill}
              onDeleteSkill={onDeleteSkill}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export default SkillNode;
