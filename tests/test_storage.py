"""Tests for storage module."""
import json
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock
from app.storage import (
    load_skills,
    save_skills,
    load_counters,
    save_counters,
    clear_all_data,
    get_next_skill_id,
    get_next_counter_id,
    SKILLS_FILE,
    COUNTERS_FILE
)
from app.models.skill import Skill
from app.models.counter import Counter


class TestLoadSkills:
    """Tests for load_skills function."""
    
    def test_load_skills_file_not_exists(self):
        """Test loading skills when file doesn't exist."""
        with patch.object(Path, 'exists', return_value=False):
            result = load_skills()
            assert result == {}
    
    def test_load_skills_success(self):
        """Test successful loading of skills."""
        mock_data = {
            "1": {"id": 1, "name": "Python", "parent_id": None},
            "2": {"id": 2, "name": "Django", "parent_id": 1}
        }
        
        with patch.object(Path, 'exists', return_value=True):
            with patch('builtins.open', mock_open(read_data=json.dumps(mock_data))):
                result = load_skills()
                
                assert len(result) == 2
                assert result[1].name == "Python"
                assert result[2].name == "Django"
                assert result[2].parent_id == 1
    
    def test_load_skills_json_decode_error(self):
        """Test handling of invalid JSON in skills file."""
        with patch.object(Path, 'exists', return_value=True):
            with patch('builtins.open', mock_open(read_data='invalid json {')):
                result = load_skills()
                assert result == {}
    
    def test_load_skills_io_error(self):
        """Test handling of IO error when loading skills."""
        with patch.object(Path, 'exists', return_value=True):
            with patch('builtins.open', side_effect=IOError("Permission denied")):
                result = load_skills()
                assert result == {}


class TestSaveSkills:
    """Tests for save_skills function."""
    
    def test_save_skills_success(self):
        """Test successful saving of skills."""
        skills = {
            1: Skill(id=1, name="Python", parent_id=None),
            2: Skill(id=2, name="Django", parent_id=1)
        }
        
        mock_file = mock_open()
        with patch('builtins.open', mock_file):
            save_skills(skills)
            
            # Verify file was opened for writing
            mock_file.assert_called_once_with(SKILLS_FILE, 'w')
            
            # Verify json.dump was called (file handle was written to)
            handle = mock_file()
            assert handle.write.called
    
    def test_save_skills_io_error(self):
        """Test handling of IO error when saving skills."""
        skills = {1: Skill(id=1, name="Python", parent_id=None)}
        
        with patch('builtins.open', side_effect=IOError("Disk full")):
            # Should not raise, just print error
            save_skills(skills)


class TestLoadCounters:
    """Tests for load_counters function."""
    
    def test_load_counters_file_not_exists(self):
        """Test loading counters when file doesn't exist."""
        with patch.object(Path, 'exists', return_value=False):
            result = load_counters()
            assert result == {}
    
    def test_load_counters_success(self):
        """Test successful loading of counters."""
        mock_data = {
            "1": {
                "id": 1,
                "skill_id": 1,
                "name": "Hours",
                "unit": "h",
                "value": 10.5,
                "target": None
            }
        }
        
        with patch.object(Path, 'exists', return_value=True):
            with patch('builtins.open', mock_open(read_data=json.dumps(mock_data))):
                result = load_counters()
                
                assert len(result) == 1
                assert result[1].name == "Hours"
                assert result[1].value == 10.5
                assert result[1].unit == "h"
    
    def test_load_counters_json_decode_error(self):
        """Test handling of invalid JSON in counters file."""
        with patch.object(Path, 'exists', return_value=True):
            with patch('builtins.open', mock_open(read_data='bad json')):
                result = load_counters()
                assert result == {}
    
    def test_load_counters_io_error(self):
        """Test handling of IO error when loading counters."""
        with patch.object(Path, 'exists', return_value=True):
            with patch('builtins.open', side_effect=IOError("File locked")):
                result = load_counters()
                assert result == {}


class TestSaveCounters:
    """Tests for save_counters function."""
    
    def test_save_counters_success(self):
        """Test successful saving of counters."""
        counters = {
            1: Counter(id=1, skill_id=1, name="Hours", unit="h", value=10.5, target=None)
        }
        
        mock_file = mock_open()
        with patch('builtins.open', mock_file):
            save_counters(counters)
            
            # Verify file was opened for writing
            mock_file.assert_called_once_with(COUNTERS_FILE, 'w')
            
            # Verify write was called
            handle = mock_file()
            assert handle.write.called
    
    def test_save_counters_io_error(self):
        """Test handling of IO error when saving counters."""
        counters = {1: Counter(id=1, skill_id=1, name="Hours", value=10.5)}
        
        with patch('builtins.open', side_effect=IOError("Read-only filesystem")):
            # Should not raise, just print error
            save_counters(counters)


class TestClearAllData:
    """Tests for clear_all_data function."""
    
    def test_clear_all_data_both_files_exist(self):
        """Test clearing data when both files exist."""
        mock_skills_path = MagicMock(spec=Path)
        mock_counters_path = MagicMock(spec=Path)
        
        mock_skills_path.exists.return_value = True
        mock_counters_path.exists.return_value = True
        
        with patch('app.storage.SKILLS_FILE', mock_skills_path):
            with patch('app.storage.COUNTERS_FILE', mock_counters_path):
                clear_all_data()
                
                mock_skills_path.unlink.assert_called_once()
                mock_counters_path.unlink.assert_called_once()
    
    def test_clear_all_data_only_skills_exists(self):
        """Test clearing data when only skills file exists."""
        mock_skills_path = MagicMock(spec=Path)
        mock_counters_path = MagicMock(spec=Path)
        
        mock_skills_path.exists.return_value = True
        mock_counters_path.exists.return_value = False
        
        with patch('app.storage.SKILLS_FILE', mock_skills_path):
            with patch('app.storage.COUNTERS_FILE', mock_counters_path):
                clear_all_data()
                
                mock_skills_path.unlink.assert_called_once()
                mock_counters_path.unlink.assert_not_called()
    
    def test_clear_all_data_only_counters_exists(self):
        """Test clearing data when only counters file exists."""
        mock_skills_path = MagicMock(spec=Path)
        mock_counters_path = MagicMock(spec=Path)
        
        mock_skills_path.exists.return_value = False
        mock_counters_path.exists.return_value = True
        
        with patch('app.storage.SKILLS_FILE', mock_skills_path):
            with patch('app.storage.COUNTERS_FILE', mock_counters_path):
                clear_all_data()
                
                mock_skills_path.unlink.assert_not_called()
                mock_counters_path.unlink.assert_called_once()
    
    def test_clear_all_data_no_files_exist(self):
        """Test clearing data when no files exist."""
        mock_skills_path = MagicMock(spec=Path)
        mock_counters_path = MagicMock(spec=Path)
        
        mock_skills_path.exists.return_value = False
        mock_counters_path.exists.return_value = False
        
        with patch('app.storage.SKILLS_FILE', mock_skills_path):
            with patch('app.storage.COUNTERS_FILE', mock_counters_path):
                clear_all_data()
                
                mock_skills_path.unlink.assert_not_called()
                mock_counters_path.unlink.assert_not_called()
    
    def test_clear_all_data_io_error(self):
        """Test handling of IO error when clearing data."""
        mock_skills_path = MagicMock(spec=Path)
        
        mock_skills_path.exists.return_value = True
        mock_skills_path.unlink.side_effect = IOError("Permission denied")
        
        with patch('app.storage.SKILLS_FILE', mock_skills_path):
            with patch('app.storage.COUNTERS_FILE', MagicMock(spec=Path)):
                # Should not raise, just print error
                clear_all_data()


class TestGetNextSkillId:
    """Tests for get_next_skill_id function."""
    
    def test_get_next_skill_id_empty_db(self):
        """Test getting next ID when database is empty."""
        result = get_next_skill_id({})
        assert result == 1
    
    def test_get_next_skill_id_with_existing_skills(self):
        """Test getting next ID with existing skills."""
        skills = {
            1: Skill(id=1, name="Python", parent_id=None),
            3: Skill(id=3, name="Java", parent_id=None),
            5: Skill(id=5, name="JavaScript", parent_id=None)
        }
        result = get_next_skill_id(skills)
        assert result == 6  # max(1, 3, 5) + 1


class TestGetNextCounterId:
    """Tests for get_next_counter_id function."""
    
    def test_get_next_counter_id_empty_db(self):
        """Test getting next ID when database is empty."""
        result = get_next_counter_id({})
        assert result == 1
    
    def test_get_next_counter_id_with_existing_counters(self):
        """Test getting next ID with existing counters."""
        counters = {
            2: Counter(id=2, skill_id=1, name="Hours", value=10),
            4: Counter(id=4, skill_id=1, name="Projects", value=5),
            7: Counter(id=7, skill_id=2, name="Exercises", value=20)
        }
        result = get_next_counter_id(counters)
        assert result == 8  # max(2, 4, 7) + 1
