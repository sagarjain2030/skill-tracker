"""Skills API router."""
from typing import Dict, List
from fastapi import APIRouter, HTTPException, status
from app.models.skill import Skill, SkillCreate

router = APIRouter(prefix="/skills", tags=["Skills"])

# In-memory storage for skills (will be replaced with database later)
skills_db: Dict[int, Skill] = {}
next_skill_id = 1


def _get_all_skills() -> Dict[int, Skill]:
    """Get all skills from storage."""
    return skills_db


def _validate_unique_root_name(name: str) -> None:
    """
    Validate that root skill name is unique.
    
    Args:
        name: The skill name to validate
        
    Raises:
        HTTPException: If a root skill with this name already exists
    """
    # Check if any root skill (parent_id=None) has this name
    for skill in skills_db.values():
        if skill.parent_id is None and skill.name.lower() == name.lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Root skill with name '{name}' already exists"
            )


@router.post("/", response_model=Skill, status_code=status.HTTP_201_CREATED)
def create_root_skill(skill_data: SkillCreate) -> Skill:
    """
    Create a new root skill.
    
    A root skill has no parent (parent_id must be None).
    Root skill names must be unique.
    
    Args:
        skill_data: The skill creation data
        
    Returns:
        The created skill
        
    Raises:
        HTTPException 400: If parent_id is not None (use subskill endpoint instead)
        HTTPException 409: If a root skill with this name already exists
    """
    global next_skill_id
    
    # Validate this is a root skill
    if skill_data.parent_id is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create subskill at this endpoint. Use POST /skills/{parent_id}/children instead."
        )
    
    # Validate unique root name
    _validate_unique_root_name(skill_data.name)
    
    # Create the skill
    skill = Skill(
        id=next_skill_id,
        name=skill_data.name,
        parent_id=None
    )
    
    skills_db[next_skill_id] = skill
    next_skill_id += 1
    
    return skill


@router.get("/", response_model=List[Skill])
def list_skills() -> List[Skill]:
    """
    List all skills.
    
    Returns:
        List of all skills
    """
    return list(skills_db.values())


@router.get("/{skill_id}", response_model=Skill)
def get_skill(skill_id: int) -> Skill:
    """
    Get a skill by ID.
    
    Args:
        skill_id: The skill ID
        
    Returns:
        The skill
        
    Raises:
        HTTPException 404: If skill not found
    """
    if skill_id not in skills_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skill with id {skill_id} not found"
        )
    
    return skills_db[skill_id]
