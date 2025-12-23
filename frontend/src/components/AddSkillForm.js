import React, { useState } from 'react';
import './AddSkillForm.css';

function AddSkillForm({ onAddSkill, parentName = null }) {
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!name.trim()) return;

    setLoading(true);
    try {
      await onAddSkill(name.trim());
      setName('');
    } catch (err) {
      console.error('Error adding skill:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="add-skill-form">
      <h3>{parentName ? `Add Subskill to ${parentName}` : 'Add Root Skill'}</h3>
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Enter skill name..."
          disabled={loading}
          maxLength={255}
        />
        <button type="submit" disabled={!name.trim() || loading}>
          {loading ? '...' : parentName ? '+ Add Subskill' : '+ Add Root Skill'}
        </button>
      </form>
    </div>
  );
}

export default AddSkillForm;
