"""
Tests for PostgreSQL storage layer (app/storage_db.py)
"""
import pytest
from app.models.skill import Skill
from app.models.counter import Counter
from app.storage_db import (
    load_skills, save_skills, load_counters, save_counters, 
    clear_all_data
)
from app.database import init_db


@pytest.fixture(autouse=True)
def setup_and_teardown():
    """Setup and teardown for each test"""
    # Initialize database before each test
    init_db()
    # Clear all data before each test
    clear_all_data()
    yield
    # Clean up after test
    clear_all_data()


def test_save_and_load_skills():
    """Test saving and loading skills from database"""
    # Create skills
    skill1 = Skill(id=1, name="Python", parent_id=None)
    skill2 = Skill(id=2, name="FastAPI", parent_id=1)
    
    skills = {1: skill1, 2: skill2}
    
    # Save to database
    save_skills(skills)
    
    # Load from database
    loaded_skills = load_skills()
    
    assert len(loaded_skills) == 2
    assert loaded_skills[1].name == "Python"
    assert loaded_skills[1].parent_id is None
    assert loaded_skills[2].name == "FastAPI"
    assert loaded_skills[2].parent_id == 1


def test_save_and_load_counters():
    """Test saving and loading counters from database"""
    # Create counters
    counter1 = Counter(id=1, skill_id=1, name="Sessions", unit="sessions", value=5.0, target=10.0)
    counter2 = Counter(id=2, skill_id=1, name="Hours", unit="hours", value=3.5, target=None)
    
    counters = {1: counter1, 2: counter2}
    
    # Save to database
    save_counters(counters)
    
    # Load from database
    loaded_counters = load_counters()
    
    assert len(loaded_counters) == 2
    assert loaded_counters[1].name == "Sessions"
    assert loaded_counters[1].value == 5.0
    assert loaded_counters[1].target == 10.0
    assert loaded_counters[2].name == "Hours"
    assert loaded_counters[2].value == 3.5
    assert loaded_counters[2].target is None


def test_clear_all_data():
    """Test clearing all data from database"""
    # Create and save skills
    skill1 = Skill(id=1, name="Python", parent_id=None)
    skills = {1: skill1}
    save_skills(skills)
    
    # Create and save counters
    counter1 = Counter(id=1, skill_id=1, name="Sessions", unit="sessions", value=5.0)
    counters = {1: counter1}
    save_counters(counters)
    
    # Clear all data
    clear_all_data()
    
    # Verify everything is cleared
    loaded_skills = load_skills()
    loaded_counters = load_counters()
    
    assert len(loaded_skills) == 0
    assert len(loaded_counters) == 0


def test_save_overwrites_existing_data():
    """Test that save operation replaces existing data"""
    # Create and save initial skills
    skill1 = Skill(id=1, name="Python", parent_id=None)
    skills = {1: skill1}
    save_skills(skills)
    
    # Create and save different skills
    skill2 = Skill(id=2, name="JavaScript", parent_id=None)
    new_skills = {2: skill2}
    save_skills(new_skills)
    
    # Load and verify
    loaded_skills = load_skills()
    
    # Should only have the new skill
    assert len(loaded_skills) == 1
    assert 1 not in loaded_skills
    assert loaded_skills[2].name == "JavaScript"


def test_load_empty_database():
    """Test loading from empty database"""
    # Clear everything
    clear_all_data()
    
    # Load from empty database
    loaded_skills = load_skills()
    loaded_counters = load_counters()
    
    assert len(loaded_skills) == 0
    assert len(loaded_counters) == 0


def test_save_skills_with_hierarchy():
    """Test saving and loading a hierarchical skill tree"""
    # Create a skill tree
    root = Skill(id=1, name="Programming", parent_id=None)
    child1 = Skill(id=2, name="Python", parent_id=1)
    child2 = Skill(id=3, name="JavaScript", parent_id=1)
    grandchild = Skill(id=4, name="FastAPI", parent_id=2)
    
    skills = {1: root, 2: child1, 3: child2, 4: grandchild}
    
    # Save and reload
    save_skills(skills)
    loaded_skills = load_skills()
    
    # Verify hierarchy is preserved
    assert len(loaded_skills) == 4
    assert loaded_skills[1].parent_id is None
    assert loaded_skills[2].parent_id == 1
    assert loaded_skills[3].parent_id == 1
    assert loaded_skills[4].parent_id == 2


def test_save_counters_with_multiple_skills():
    """Test saving counters for multiple skills"""
    # Create counters for different skills
    counter1 = Counter(id=1, skill_id=1, name="Sessions", unit="sessions", value=5.0)
    counter2 = Counter(id=2, skill_id=1, name="Hours", unit="hours", value=3.5)
    counter3 = Counter(id=3, skill_id=2, name="Projects", unit="projects", value=2.0)
    
    counters = {1: counter1, 2: counter2, 3: counter3}
    
    # Save and reload
    save_counters(counters)
    loaded_counters = load_counters()
    
    # Verify all counters are preserved
    assert len(loaded_counters) == 3
    assert loaded_counters[1].skill_id == 1
    assert loaded_counters[2].skill_id == 1
    assert loaded_counters[3].skill_id == 2


def test_counter_target_persistence():
    """Test that counter targets are properly persisted"""
    # Create counters with and without targets
    counter1 = Counter(id=1, skill_id=1, name="Sessions", unit="sessions", value=5.0, target=10.0)
    counter2 = Counter(id=2, skill_id=1, name="Hours", unit="hours", value=3.5, target=None)
    counter3 = Counter(id=3, skill_id=1, name="Days", unit="days", value=7.0, target=30.0)
    
    counters = {1: counter1, 2: counter2, 3: counter3}
    
    # Save and reload
    save_counters(counters)
    loaded_counters = load_counters()
    
    # Verify targets are preserved correctly
    assert loaded_counters[1].target == 10.0
    assert loaded_counters[2].target is None
    assert loaded_counters[3].target == 30.0


def test_database_persistence_across_operations():
    """Test that data persists across multiple save/load operations"""
    # First operation: Save some skills
    skill1 = Skill(id=1, name="Python", parent_id=None)
    save_skills({1: skill1})
    
    # Second operation: Add a counter
    counter1 = Counter(id=1, skill_id=1, name="Sessions", unit="sessions", value=5.0)
    save_counters({1: counter1})
    
    # Load both and verify
    loaded_skills = load_skills()
    loaded_counters = load_counters()
    
    assert len(loaded_skills) == 1
    assert len(loaded_counters) == 1
    assert loaded_skills[1].name == "Python"
    assert loaded_counters[1].name == "Sessions"
    
    # Third operation: Update skills
    skill2 = Skill(id=2, name="JavaScript", parent_id=None)
    save_skills({1: skill1, 2: skill2})
    
    # Verify counters still exist
    loaded_skills = load_skills()
    loaded_counters = load_counters()
    
    assert len(loaded_skills) == 2
    assert len(loaded_counters) == 1  # Counters should still be there
