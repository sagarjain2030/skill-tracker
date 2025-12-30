"""Storage layer that works with both PostgreSQL and in-memory fallback."""
from typing import Dict
from sqlalchemy.orm import Session
from app.database import SessionLocal, SkillDB, CounterDB, init_db
from app.models.skill import Skill
from app.models.counter import Counter


# Initialize database on module load
try:
    init_db()
    print("✅ Database initialized successfully")
except Exception as e:
    print(f"⚠️  Database initialization warning: {e}")


def get_db_session() -> Session:
    """Get a new database session."""
    return SessionLocal()


# Skills storage functions
def load_skills() -> Dict[int, Skill]:
    """Load all skills from database."""
    db = get_db_session()
    try:
        db_skills = db.query(SkillDB).all()
        return {
            skill.id: Skill(
                id=skill.id,
                name=skill.name,
                parent_id=skill.parent_id
            )
            for skill in db_skills
        }
    finally:
        db.close()


def save_skills(skills_db: Dict[int, Skill]) -> None:
    """Save all skills to database."""
    db = get_db_session()
    try:
        # Clear existing skills
        db.query(SkillDB).delete()
        
        # Insert all skills
        for skill in skills_db.values():
            db_skill = SkillDB(
                id=skill.id,
                name=skill.name,
                parent_id=skill.parent_id
            )
            db.add(db_skill)
        
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


def get_next_skill_id(skills_db: Dict[int, Skill]) -> int:
    """Get the next available skill ID."""
    if not skills_db:
        return 1
    return max(skills_db.keys()) + 1


# Counters storage functions
def load_counters() -> Dict[int, Counter]:
    """Load all counters from database."""
    db = get_db_session()
    try:
        db_counters = db.query(CounterDB).all()
        return {
            counter.id: Counter(
                id=counter.id,
                skill_id=counter.skill_id,
                name=counter.name,
                unit=counter.unit,
                value=counter.value,
                target=counter.target
            )
            for counter in db_counters
        }
    finally:
        db.close()


def save_counters(counters_db: Dict[int, Counter]) -> None:
    """Save all counters to database."""
    db = get_db_session()
    try:
        # Clear existing counters
        db.query(CounterDB).delete()
        
        # Insert all counters
        for counter in counters_db.values():
            db_counter = CounterDB(
                id=counter.id,
                skill_id=counter.skill_id,
                name=counter.name,
                unit=counter.unit,
                value=counter.value,
                target=counter.target
            )
            db.add(db_counter)
        
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


def get_next_counter_id(counters_db: Dict[int, Counter]) -> int:
    """Get the next available counter ID."""
    if not counters_db:
        return 1
    return max(counters_db.keys()) + 1


# Clear all data
def clear_all_data() -> None:
    """Clear all data from database."""
    db = get_db_session()
    try:
        db.query(CounterDB).delete()
        db.query(SkillDB).delete()
        db.commit()
        print("✅ All data cleared from database")
    except Exception as e:
        db.rollback()
        print(f"⚠️  Error clearing database: {e}")
        raise e
    finally:
        db.close()
