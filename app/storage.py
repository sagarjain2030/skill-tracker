"""Persistent storage management for skills and counters."""
import json
import os
from pathlib import Path
from typing import Dict
from app.models.skill import Skill
from app.models.counter import Counter

# Storage directory
STORAGE_DIR = Path("data")
SKILLS_FILE = STORAGE_DIR / "skills.json"
COUNTERS_FILE = STORAGE_DIR / "counters.json"

# Ensure storage directory exists
STORAGE_DIR.mkdir(exist_ok=True)


def load_skills() -> Dict[int, Skill]:
    """Load skills from persistent storage."""
    if not SKILLS_FILE.exists():
        return {}
    
    try:
        with open(SKILLS_FILE, 'r') as f:
            data = json.load(f)
            return {int(k): Skill(**v) for k, v in data.items()}
    except (json.JSONDecodeError, IOError) as e:
        print(f"Warning: Could not load skills from {SKILLS_FILE}: {e}")
        return {}


def save_skills(skills_db: Dict[int, Skill]) -> None:
    """Save skills to persistent storage."""
    try:
        data = {str(k): v.model_dump() for k, v in skills_db.items()}
        with open(SKILLS_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except IOError as e:
        print(f"Error: Could not save skills to {SKILLS_FILE}: {e}")


def load_counters() -> Dict[int, Counter]:
    """Load counters from persistent storage."""
    if not COUNTERS_FILE.exists():
        return {}
    
    try:
        with open(COUNTERS_FILE, 'r') as f:
            data = json.load(f)
            return {int(k): Counter(**v) for k, v in data.items()}
    except (json.JSONDecodeError, IOError) as e:
        print(f"Warning: Could not load counters from {COUNTERS_FILE}: {e}")
        return {}


def save_counters(counters_db: Dict[int, Counter]) -> None:
    """Save counters to persistent storage."""
    try:
        data = {str(k): v.model_dump() for k, v in counters_db.items()}
        with open(COUNTERS_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except IOError as e:
        print(f"Error: Could not save counters to {COUNTERS_FILE}: {e}")


def clear_all_data() -> None:
    """Delete all persisted data files."""
    try:
        if SKILLS_FILE.exists():
            SKILLS_FILE.unlink()
        if COUNTERS_FILE.exists():
            COUNTERS_FILE.unlink()
    except IOError as e:
        print(f"Error: Could not clear data: {e}")


def get_next_skill_id(skills_db: Dict[int, Skill]) -> int:
    """Get the next available skill ID."""
    if not skills_db:
        return 1
    return max(skills_db.keys()) + 1


def get_next_counter_id(counters_db: Dict[int, Counter]) -> int:
    """Get the next available counter ID."""
    if not counters_db:
        return 1
    return max(counters_db.keys()) + 1
