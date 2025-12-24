"""Skills API router."""
from typing import Dict, List
from fastapi import APIRouter, HTTPException, status
from app.models.skill import Skill, SkillCreate, SkillUpdate, SkillWithChildren
from app.utils.validation import validate_no_cycle, get_descendants, CyclicDependencyError
from app.storage import load_skills, save_skills, get_next_skill_id

router = APIRouter(prefix="/skills", tags=["Skills"])

# Load skills from persistent storage
skills_db: Dict[int, Skill] = load_skills()
next_skill_id = get_next_skill_id(skills_db)


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
    save_skills(skills_db)
    
    return skill


@router.get("/", response_model=List[Skill])
def list_skills() -> List[Skill]:
    """
    List all skills.
    
    Returns:
        List of all skills
    """
    return list(skills_db.values())


@router.get("/tree", response_model=List[SkillWithChildren])
def get_skill_tree() -> List[SkillWithChildren]:
    """
    Get the complete skill hierarchy as a tree structure.
    
    Returns only root skills (skills with no parent), with all their
    descendants nested in the 'children' field recursively.
    
    Returns:
        List of root skills with nested children
    """
    def build_skill_tree(skill_id: int) -> SkillWithChildren:
        """Recursively build a skill tree from a skill ID."""
        skill = skills_db[skill_id]
        
        # Find all direct children
        children_ids = [
            sid for sid, s in skills_db.items() 
            if s.parent_id == skill_id
        ]
        
        # Recursively build children
        children = [build_skill_tree(child_id) for child_id in children_ids]
        
        return SkillWithChildren(
            id=skill.id,
            name=skill.name,
            parent_id=skill.parent_id,
            children=children
        )
    
    # Find all root skills (parent_id is None)
    root_ids = [sid for sid, skill in skills_db.items() if skill.parent_id is None]
    
    # Build tree for each root
    return [build_skill_tree(root_id) for root_id in root_ids]


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


@router.get("/{skill_id}/tree", response_model=SkillWithChildren)
def get_skill_subtree(skill_id: int) -> SkillWithChildren:
    """
    Get a skill and all its descendants as a tree structure.
    
    Returns the specified skill with all its descendants nested
    in the 'children' field recursively.
    
    Args:
        skill_id: The ID of the skill to get the subtree for
        
    Returns:
        The skill with nested children
        
    Raises:
        HTTPException 404: If skill not found
    """
    # Check skill exists
    if skill_id not in skills_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skill with id {skill_id} not found"
        )
    
    def build_skill_tree(sid: int) -> SkillWithChildren:
        """Recursively build a skill tree from a skill ID."""
        skill = skills_db[sid]
        
        # Find all direct children
        children_ids = [
            child_id for child_id, s in skills_db.items() 
            if s.parent_id == sid
        ]
        
        # Recursively build children
        children = [build_skill_tree(child_id) for child_id in children_ids]
        
        return SkillWithChildren(
            id=skill.id,
            name=skill.name,
            parent_id=skill.parent_id,
            children=children
        )
    
    return build_skill_tree(skill_id)


@router.post("/{parent_id}/children", response_model=Skill, status_code=status.HTTP_201_CREATED)
def create_subskill(parent_id: int, skill_data: SkillCreate) -> Skill:
    """
    Create a new subskill under a parent skill.
    
    A subskill has a parent (parent_id is set to the parent skill's ID).
    Validates that no cyclic dependencies are created.
    
    Args:
        parent_id: The ID of the parent skill
        skill_data: The skill creation data
        
    Returns:
        The created subskill
        
    Raises:
        HTTPException 400: If parent_id in skill_data doesn't match URL parameter
        HTTPException 404: If parent skill not found
        HTTPException 409: If creating the subskill would create a cycle
    """
    global next_skill_id
    
    # Validate parent exists
    if parent_id not in skills_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Parent skill with id {parent_id} not found"
        )
    
    # If parent_id is provided in body, it must match the URL parameter
    if skill_data.parent_id is not None and skill_data.parent_id != parent_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Parent ID in request body ({skill_data.parent_id}) does not match URL parameter ({parent_id})"
        )
    
    # Create skill with parent_id from URL
    new_skill_id = next_skill_id
    temp_skill = Skill(
        id=new_skill_id,
        name=skill_data.name,
        parent_id=parent_id
    )
    
    # Create temporary skill parent map for validation (ID -> parent_id)
    temp_skill_parent_map = {skill_id: skill.parent_id for skill_id, skill in skills_db.items()}
    temp_skill_parent_map[new_skill_id] = parent_id
    
    # Validate no cycles would be created
    try:
        validate_no_cycle(new_skill_id, parent_id, temp_skill_parent_map)
    except CyclicDependencyError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    
    # Add to database
    skills_db[new_skill_id] = temp_skill
    next_skill_id += 1
    save_skills(skills_db)
    
    return temp_skill


@router.patch("/{skill_id}", response_model=Skill)
def update_skill(skill_id: int, skill_data: SkillUpdate) -> Skill:
    """
    Update an existing skill's metadata.
    
    Can update name and/or parent_id. When updating parent_id:
    - Use None to keep current parent
    - Use -1 to convert to root skill (set parent_id to None)
    - Use a valid skill ID to set as parent (validates no cycles)
    
    Args:
        skill_id: The ID of the skill to update
        skill_data: The update data (name and/or parent_id)
        
    Returns:
        The updated skill
        
    Raises:
        HTTPException 404: If skill not found
        HTTPException 400: If new parent doesn't exist
        HTTPException 409: If updating parent would create a cycle
    """
    # Check skill exists
    if skill_id not in skills_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skill with id {skill_id} not found"
        )
    
    existing_skill = skills_db[skill_id]
    
    # Determine new parent_id
    # If parent_id is explicitly in the update data (even if None), use it
    # Special case: -1 means "set to root" (parent_id = None)
    if skill_data.parent_id == -1:
        new_parent_id = None
    elif "parent_id" in skill_data.model_dump(exclude_unset=True):
        new_parent_id = skill_data.parent_id
    else:
        new_parent_id = existing_skill.parent_id
    
    # Validate new parent exists (if not None)
    if new_parent_id is not None and new_parent_id not in skills_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Parent skill with id {new_parent_id} not found"
        )
    
    # If parent is changing, validate no cycles
    if new_parent_id != existing_skill.parent_id:
        # Create temporary parent map with the proposed change
        temp_skill_parent_map = {sid: s.parent_id for sid, s in skills_db.items()}
        temp_skill_parent_map[skill_id] = new_parent_id
        
        try:
            validate_no_cycle(skill_id, new_parent_id, temp_skill_parent_map)
        except CyclicDependencyError as e:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e)
            )
    
    # Update skill
    updated_skill = Skill(
        id=existing_skill.id,
        name=skill_data.name if skill_data.name is not None else existing_skill.name,
        parent_id=new_parent_id
    )
    
    skills_db[skill_id] = updated_skill
    save_skills(skills_db)
    return updated_skill


@router.delete("/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_skill(skill_id: int) -> None:
    """
    Delete a skill and all its descendants (entire subtree).
    
    This operation cascades - deleting a skill will also delete all its children,
    grandchildren, and so on. This ensures referential integrity is maintained.
    
    Args:
        skill_id: The ID of the skill to delete
        
    Returns:
        None (204 No Content on success)
        
    Raises:
        HTTPException 404: If skill not found
        
    Examples:
        Given hierarchy: A -> B -> C, D
        - Deleting C removes only C
        - Deleting B removes B, C, and D
        - Deleting A removes A, B, C, and D
    """
    # Check skill exists
    if skill_id not in skills_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skill with id {skill_id} not found"
        )
    
    # Get all descendants to delete
    skill_parent_map = {sid: s.parent_id for sid, s in skills_db.items()}
    descendants = get_descendants(skill_id, skill_parent_map)
    
    # Delete the skill and all descendants
    skills_to_delete = {skill_id} | descendants
    for sid in skills_to_delete:
        del skills_db[sid]
    save_skills(skills_db)
    
    # Return None for 204 No Content
    return None
