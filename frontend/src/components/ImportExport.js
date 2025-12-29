import React, { useRef, useState } from 'react';
import skillService from '../services/api';
import './ImportExport.css';

function ImportExport({ onImport }) {
  const fileInputRef = useRef(null);
  const replaceInputRef = useRef(null);
  const [importing, setImporting] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [error, setError] = useState(null);

  const handleExport = async () => {
    try {
      setExporting(true);
      setError(null);
      
      const data = await skillService.exportSkillTree();
      
      // Create blob and download
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `skills-export-${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to export skills');
      console.error('Export error:', err);
    } finally {
      setExporting(false);
    }
  };

  const handleImportClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      setImporting(true);
      setError(null);

      const text = await file.text();
      const data = JSON.parse(text);

      // Validate format
      if (!Array.isArray(data)) {
        throw new Error('Invalid format: JSON must be an array of skill trees');
      }

      // Validate each tree has required fields
      data.forEach((tree, idx) => {
        if (!tree.name) {
          throw new Error(`Tree at index ${idx} missing 'name' field`);
        }
        if (!Array.isArray(tree.children)) {
          throw new Error(`Tree at index ${idx} missing or invalid 'children' array`);
        }
      });

      const confirmed = window.confirm(
        `Import ${data.length} skill tree(s)?\n\nThis will add them to your existing skills.`
      );

      if (confirmed) {
        await skillService.importSkillTree(data);
        onImport();
      }
    } catch (err) {
      if (err instanceof SyntaxError) {
        setError('Invalid JSON file');
      } else {
        setError(err.message || err.response?.data?.detail || 'Failed to import skills');
      }
      console.error('Import error:', err);
    } finally {
      setImporting(false);
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleReplaceClick = () => {
    replaceInputRef.current?.click();
  };

  const handleReplaceChange = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      setImporting(true);
      setError(null);

      const text = await file.text();
      const data = JSON.parse(text);

      // Validate format
      if (!Array.isArray(data)) {
        throw new Error('Invalid format: JSON must be an array of skill trees');
      }

      // Validate each tree has required fields
      data.forEach((tree, idx) => {
        if (!tree.name) {
          throw new Error(`Tree at index ${idx} missing 'name' field`);
        }
        if (!Array.isArray(tree.children)) {
          throw new Error(`Tree at index ${idx} missing or invalid 'children' array`);
        }
      });

      const confirmed = window.confirm(
        '⚠️ WARNING: This will DELETE ALL existing skills and replace them.\n\n' +
        `Import ${data.length} skill tree(s) and delete everything else?\n\n` +
        'This action cannot be undone!'
      );

      if (confirmed) {
        await skillService.updateSkillTree(data);
        onImport();
      }
    } catch (err) {
      if (err instanceof SyntaxError) {
        setError('Invalid JSON file');
      } else {
        setError(err.message || err.response?.data?.detail || 'Failed to replace skills');
      }
      console.error('Replace error:', err);
    } finally {
      setImporting(false);
      // Reset file input
      if (replaceInputRef.current) {
        replaceInputRef.current.value = '';
      }
    }
  };

  return (
    <div className="import-export">
      <div className="import-export-buttons">
        <button
          onClick={handleExport}
          disabled={exporting}
          className="btn-export"
          title="Export all skills as JSON"
        >
          {exporting ? '⏳ Exporting...' : '📥 Export'}
        </button>

        <button
          onClick={handleImportClick}
          disabled={importing}
          className="btn-import"
          title="Import skills from JSON (adds to existing)"
        >
          {importing ? '⏳ Importing...' : '📤 Import'}
        </button>

        <button
          onClick={handleReplaceClick}
          disabled={importing}
          className="btn-replace"
          title="⚠️ Replace ALL skills (deletes existing)"
        >
          {importing ? '⏳ Replacing...' : '🔄 Replace All'}
        </button>

        <input
          ref={fileInputRef}
          type="file"
          accept=".json,application/json"
          onChange={handleFileChange}
          style={{ display: 'none' }}
        />

        <input
          ref={replaceInputRef}
          type="file"
          accept=".json,application/json"
          onChange={handleReplaceChange}
          style={{ display: 'none' }}
        />
      </div>

      {error && (
        <div className="import-export-error">
          ❌ {error}
        </div>
      )}

      <div className="import-export-hint">
        💡 Export to backup, Import to add skills, Replace All to restore from backup
      </div>
    </div>
  );
}

export default ImportExport;
