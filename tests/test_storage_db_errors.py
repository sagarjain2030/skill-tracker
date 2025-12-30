"""
Additional tests for storage_db error handling and edge cases.
"""
import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.exc import SQLAlchemyError
from app.models.skill import Skill
from app.models.counter import Counter
from app.storage_db import (
    save_skills, save_counters, clear_all_data,
    get_next_skill_id, get_next_counter_id
)


def test_save_skills_database_error_rollback():
    """Test that database errors trigger rollback in save_skills"""
    skill1 = Skill(id=1, name="Python", parent_id=None)
    skills = {1: skill1}
    
    # Mock the database session to raise an error during commit
    with patch('app.storage_db.get_db_session') as mock_get_db:
        mock_session = MagicMock()
        mock_session.commit.side_effect = SQLAlchemyError("Database error")
        mock_get_db.return_value = mock_session
        
        # Should raise the exception
        with pytest.raises(SQLAlchemyError):
            save_skills(skills)
        
        # Verify rollback was called
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()


def test_save_counters_database_error_rollback():
    """Test that database errors trigger rollback in save_counters"""
    counter1 = Counter(id=1, skill_id=1, name="Sessions", unit="sessions", value=5.0)
    counters = {1: counter1}
    
    # Mock the database session to raise an error during commit
    with patch('app.storage_db.get_db_session') as mock_get_db:
        mock_session = MagicMock()
        mock_session.commit.side_effect = SQLAlchemyError("Database error")
        mock_get_db.return_value = mock_session
        
        # Should raise the exception
        with pytest.raises(SQLAlchemyError):
            save_counters(counters)
        
        # Verify rollback was called
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()


def test_clear_all_data_database_error_rollback():
    """Test that database errors trigger rollback in clear_all_data"""
    # Mock the database session to raise an error during commit
    with patch('app.storage_db.get_db_session') as mock_get_db:
        mock_session = MagicMock()
        mock_session.commit.side_effect = SQLAlchemyError("Database error")
        mock_get_db.return_value = mock_session
        
        # Should raise the exception
        with pytest.raises(SQLAlchemyError):
            clear_all_data()
        
        # Verify rollback was called
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()


def test_get_next_skill_id_empty_database():
    """Test get_next_skill_id with empty database"""
    result = get_next_skill_id({})
    assert result == 1


def test_get_next_skill_id_with_existing_skills():
    """Test get_next_skill_id with existing skills"""
    skills = {
        1: Skill(id=1, name="Python", parent_id=None),
        3: Skill(id=3, name="JavaScript", parent_id=None),
        5: Skill(id=5, name="Rust", parent_id=None)
    }
    result = get_next_skill_id(skills)
    assert result == 6  # max(1, 3, 5) + 1


def test_get_next_counter_id_empty_database():
    """Test get_next_counter_id with empty database"""
    result = get_next_counter_id({})
    assert result == 1


def test_get_next_counter_id_with_existing_counters():
    """Test get_next_counter_id with existing counters"""
    counters = {
        2: Counter(id=2, skill_id=1, name="Sessions", unit="sessions", value=5.0),
        4: Counter(id=4, skill_id=1, name="Hours", unit="hours", value=3.0),
        7: Counter(id=7, skill_id=2, name="Days", unit="days", value=10.0)
    }
    result = get_next_counter_id(counters)
    assert result == 8  # max(2, 4, 7) + 1


def test_clear_all_data_error_message(capsys):
    """Test that clear_all_data prints error message on failure"""
    # Mock the database session to raise an error
    with patch('app.storage_db.get_db_session') as mock_get_db:
        mock_session = MagicMock()
        mock_session.commit.side_effect = SQLAlchemyError("Database error")
        mock_get_db.return_value = mock_session
        
        # Should raise the exception
        with pytest.raises(SQLAlchemyError):
            clear_all_data()
        
        # Check the printed error message
        captured = capsys.readouterr()
        assert "⚠️  Error clearing database" in captured.out
