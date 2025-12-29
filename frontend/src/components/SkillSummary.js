import React, { useState, useEffect, useCallback } from 'react';
import skillService from '../services/api';
import './SkillSummary.css';

function SkillSummary({ skillId, onClose }) {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadSummary = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await skillService.getSkillSummary(skillId);
      setSummary(data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load summary');
      console.error('Error loading summary:', err);
    } finally {
      setLoading(false);
    }
  }, [skillId]);

  useEffect(() => {
    loadSummary();
  }, [loadSummary]);

  const renderCounterTotals = (counterTotals) => {
    if (!counterTotals || counterTotals.length === 0) {
      return <p className="no-counters">No counters tracked</p>;
    }

    return (
      <div className="counter-totals">
        {counterTotals.map((counter, idx) => (
          <div key={idx} className="counter-card">
            <div className="counter-header">
              <span className="counter-name">{counter.name}</span>
              {counter.unit && <span className="counter-unit">({counter.unit})</span>}
            </div>
            <div className="counter-value">{counter.total.toFixed(1)}</div>
            <div className="counter-meta">
              <span className="counter-count">
                📊 {counter.count} {counter.count === 1 ? 'counter' : 'counters'}
              </span>
            </div>
          </div>
        ))}
      </div>
    );
  };

  const renderChildSummary = (child, level = 0) => {
    return (
      <div key={child.id} className="child-summary" style={{ marginLeft: `${level * 20}px` }}>
        <div className="child-header">
          <span className="child-name">
            {level > 0 && '└─ '}
            {child.name}
          </span>
          <div className="child-stats">
            {child.direct_children_count > 0 && (
              <span className="stat-badge">
                👶 {child.direct_children_count} {child.direct_children_count === 1 ? 'child' : 'children'}
              </span>
            )}
            {child.counter_totals.length > 0 && (
              <span className="stat-badge">
                📊 {child.counter_totals.length} {child.counter_totals.length === 1 ? 'counter' : 'counters'}
              </span>
            )}
          </div>
        </div>
        
        {child.counter_totals.length > 0 && (
          <div className="child-counters">
            {child.counter_totals.map((counter, idx) => (
              <span key={idx} className="mini-counter">
                {counter.name}: {counter.total.toFixed(1)} {counter.unit || ''}
              </span>
            ))}
          </div>
        )}

        {child.children && child.children.length > 0 && (
          <div className="nested-children">
            {child.children.map(grandchild => renderChildSummary(grandchild, level + 1))}
          </div>
        )}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="summary-container">
        <div className="summary-header">
          <h2>Loading Summary...</h2>
          <button className="close-btn" onClick={onClose}>✕</button>
        </div>
        <div className="loading-spinner">Loading...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="summary-container">
        <div className="summary-header">
          <h2>Error</h2>
          <button className="close-btn" onClick={onClose}>✕</button>
        </div>
        <div className="error-message">{error}</div>
      </div>
    );
  }

  if (!summary) return null;

  return (
    <div className="summary-container">
      <div className="summary-header">
        <h2>📋 Summary: {summary.name}</h2>
        <button className="close-btn" onClick={onClose}>✕</button>
      </div>

      <div className="summary-content">
        {/* Overview Stats */}
        <div className="overview-section">
          <h3>Overview</h3>
          <div className="stats-grid">
            <div className="stat-card">
              <div className="stat-label">Direct Children</div>
              <div className="stat-value">{summary.direct_children_count}</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Total Descendants</div>
              <div className="stat-value">{summary.total_descendants}</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Counter Types</div>
              <div className="stat-value">{summary.counter_totals.length}</div>
            </div>
          </div>
        </div>

        {/* Counter Totals */}
        <div className="counters-section">
          <h3>📊 Aggregated Counters</h3>
          <p className="section-description">
            Total values including this skill and all {summary.total_descendants} descendant{summary.total_descendants !== 1 ? 's' : ''}
          </p>
          {renderCounterTotals(summary.counter_totals)}
        </div>

        {/* Children Breakdown */}
        {summary.children && summary.children.length > 0 && (
          <div className="children-section">
            <h3>🌳 Skill Breakdown</h3>
            <div className="children-list">
              {summary.children.map(child => renderChildSummary(child))}
            </div>
          </div>
        )}

        {summary.total_descendants === 0 && summary.counter_totals.length === 0 && (
          <div className="empty-state">
            <p>📝 This skill has no counters or descendants yet.</p>
            <p>Add counters or create subskills in the tree view.</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default SkillSummary;
