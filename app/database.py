"""Database configuration and models using SQLAlchemy."""
import os
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship, declarative_base

# Database URL - use PostgreSQL on Render, SQLite locally
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./data/skill_tracker.db"  # Fallback for local development
)

# Fix for Render's postgres:// URL (needs to be postgresql://)
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    echo=False  # Set to True for SQL query debugging
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()


# Database Models
class SkillDB(Base):
    """Skill table model."""
    __tablename__ = "skills"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    parent_id = Column(Integer, ForeignKey("skills.id"), nullable=True, index=True)
    
    # Relationships
    counters = relationship("CounterDB", back_populates="skill", cascade="all, delete-orphan")


class CounterDB(Base):
    """Counter table model."""
    __tablename__ = "counters"
    
    id = Column(Integer, primary_key=True, index=True)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    unit = Column(String(50), nullable=True)
    value = Column(Float, nullable=False, default=0.0)
    target = Column(Float, nullable=True)
    
    # Relationships
    skill = relationship("SkillDB", back_populates="counters")


def init_db():
    """Initialize database - create all tables."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Get database session dependency for FastAPI."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
