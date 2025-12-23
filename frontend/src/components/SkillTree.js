import React, { useState } from 'react';
import SkillNode from './SkillNode';
import './SkillTree.css';

function SkillTree({ skills, onAddSubskill, onUpdateSkill, onDeleteSkill }) {
  const [expandedNodes, setExpandedNodes] = useState(new Set());

  const toggleNode = (id) => {
    setExpandedNodes(prev => {
      const newSet = new Set(prev);
      if (newSet.has(id)) {
        newSet.delete(id);
      } else {
        newSet.add(id);
      }
      return newSet;
    });
  };

  const expandAll = () => {
    const allIds = new Set();
    const collectIds = (nodes) => {
      nodes.forEach(node => {
        if (node.children && node.children.length > 0) {
          allIds.add(node.id);
          collectIds(node.children);
        }
      });
    };
    collectIds(skills);
    setExpandedNodes(allIds);
  };

  const collapseAll = () => {
    setExpandedNodes(new Set());
  };

  return (
    <div className="skill-tree">
      <div className="tree-header">
        <h2>Skill Hierarchy</h2>
        <div className="tree-controls">
          <button onClick={expandAll} className="control-btn">
            Expand All
          </button>
          <button onClick={collapseAll} className="control-btn">
            Collapse All
          </button>
        </div>
      </div>

      <div className="tree-content">
        {skills.map(skill => (
          <SkillNode
            key={skill.id}
            skill={skill}
            level={0}
            isExpanded={expandedNodes.has(skill.id)}
            onToggle={toggleNode}
            onAddSubskill={onAddSubskill}
            onUpdateSkill={onUpdateSkill}
            onDeleteSkill={onDeleteSkill}
          />
        ))}
      </div>
    </div>
  );
}

export default SkillTree;
