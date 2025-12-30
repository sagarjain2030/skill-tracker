"""Skills API router."""
from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException, status
from app.models.skill import (
    Skill, SkillCreate, SkillUpdate, SkillWithChildren, 
    SkillSummary, CounterSummary, SkillImportNode, SkillExportNode, CounterExportData
)
from app.models.counter import Counter
from app.utils.validation import validate_no_cycle, get_descendants, CyclicDependencyError
from app.storage_db import load_skills, save_skills, get_next_skill_id

router = APIRouter(prefix="/skills", tags=["Skills"])

# Load skills from database
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


@router.post("/import", response_model=List[SkillExportNode], status_code=status.HTTP_201_CREATED)
def import_skill_tree(trees: List[SkillImportNode]) -> List[SkillExportNode]:
    """
    Import one or more skill trees from JSON.
    
    Creates entire skill hierarchies from JSON structure. Each tree is created as
    a separate root skill with its nested children.
    
    Args:
        trees: List of skill trees to import (each becomes a root skill)
        
    Returns:
        List of created trees with assigned IDs
        
    Raises:
        HTTPException 409: If a root skill name already exists
    """
    global next_skill_id
    from app.routers.counters import counters_db, save_counters
    
    result = []
    for tree in trees:
        result.append(_import_tree_node(tree, None))
    
    # Save to storage
    save_skills(skills_db)
    save_counters(counters_db)
    
    return result


@router.get("/export", response_model=List[SkillExportNode])
def export_skill_tree() -> List[SkillExportNode]:
    """
    Export all skill trees as JSON.
    
    Returns the complete skill hierarchy as a list of root skills with
    nested children. Can be used for backup or sharing skill trees.
    
    Returns:
        List of root skill trees with nested children
    """
    from app.routers.counters import counters_db
    
    def export_node(skill_id: int) -> SkillExportNode:
        """Recursively export a skill node and its children."""
        skill = skills_db[skill_id]
        
        # Find children
        children = [
            export_node(child_id) 
            for child_id, child_skill in skills_db.items() 
            if child_skill.parent_id == skill_id
        ]
        
        # Get counters for this skill
        skill_counters = [
            CounterExportData(
                name=counter.name,
                unit=counter.unit,
                value=counter.value,
                target=counter.target
            )
            for counter_id, counter in counters_db.items()
            if counter.skill_id == skill_id
        ]
        
        return SkillExportNode(
            id=skill.id,
            name=skill.name,
            counters=skill_counters,
            children=children
        )
    
    # Find all root skills
    root_ids = [skill_id for skill_id, skill in skills_db.items() if skill.parent_id is None]
    
    # Export each root tree
    return [export_node(root_id) for root_id in root_ids]


@router.put("/import", response_model=List[SkillExportNode])
def update_skill_tree(trees: List[SkillImportNode]) -> List[SkillExportNode]:
    """
    Update/replace all skill trees with imported JSON.
    
    WARNING: This clears all existing skills and replaces them with the imported trees.
    Use this for restoring backups or complete tree replacements.
    
    Args:
        trees: List of skill trees to import (replaces all existing skills)
        
    Returns:
        List of created trees with assigned IDs
    """
    global next_skill_id
    from app.routers.counters import counters_db, save_counters
    
    # Clear all existing skills and counters
    skills_db.clear()
    counters_db.clear()
    next_skill_id = 1
    # Note: We need to reset next_counter_id in the counters module
    import app.routers.counters as counters_module
    counters_module.next_counter_id = 1
    
    # Import all trees
    result = []
    for tree in trees:
        result.append(_import_tree_node(tree, None))
    
    # Save to storage
    save_skills(skills_db)
    save_counters(counters_db)
    
    return result


def _import_tree_node(node: SkillImportNode, parent_id: Optional[int]) -> SkillExportNode:
    """Recursively import a skill node and its children."""
    global next_skill_id
    from app.routers.counters import counters_db
    import app.routers.counters as counters_module
    
    # Validate unique root name
    if parent_id is None:
        _validate_unique_root_name(node.name)
    
    # Create skill
    skill = Skill(
        id=next_skill_id,
        name=node.name,
        parent_id=parent_id
    )
    skills_db[skill.id] = skill
    skill_id = skill.id
    next_skill_id += 1
    
    # Create counters for this skill
    counter_exports = []
    for counter_data in node.counters:
        counter = Counter(
            id=counters_module.next_counter_id,
            skill_id=skill_id,
            name=counter_data.get("name", ""),
            unit=counter_data.get("unit"),
            value=float(counter_data.get("value", 0)),
            target=float(counter_data["target"]) if counter_data.get("target") is not None else None
        )
        counters_db[counter.id] = counter
        counters_module.next_counter_id += 1
        
        counter_exports.append(CounterExportData(
            name=counter.name,
            unit=counter.unit,
            value=counter.value,
            target=counter.target
        ))
    
    # Recursively import children
    children_exports = [_import_tree_node(child, skill_id) for child in node.children]
    
    return SkillExportNode(
        id=skill_id,
        name=skill.name,
        counters=counter_exports,
        children=children_exports
    )


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


@router.get("/roots/summary", response_model=List[SkillSummary])
def get_roots_summary() -> List[SkillSummary]:
    """
    Get aggregated summaries for all root skills.
    
    This endpoint provides a comprehensive overview of all skill trees by returning
    summary data for each root skill (skills with no parent). Each summary includes:
    - Skill basic information (id, name, parent_id)
    - Aggregated counter totals across the entire tree
    - Descendant counts and recursive children summaries
    
    Returns:
        List of SkillSummary objects, one for each root skill
        
    Example use cases:
        - Dashboard overview of all skill trees
        - Comparing progress across different skill domains
        - Total effort tracking across all skills
    """
    # Get all root skills (parent_id is None)
    root_skills = [skill for skill in skills_db.values() if skill.parent_id is None]
    
    # Get summary for each root skill
    root_summaries = [get_skill_summary(root.id) for root in root_skills]
    
    return root_summaries


@router.get("/{skill_id}/summary", response_model=SkillSummary)
def get_skill_summary(skill_id: int) -> SkillSummary:
    """
    Get a comprehensive summary of a skill including aggregated counter data and children.
    
    This endpoint provides:
    - Skill basic information (id, name, parent_id)
    - Aggregated counter totals (sum of all counters with same name+unit across this skill and descendants)
    - Child count and total descendants count
    - Recursive children summaries
    
    Args:
        skill_id: The ID of the skill to summarize
        
    Returns:
        SkillSummary with aggregated data
        
    Raises:
        HTTPException 404: If skill not found
    """
    from app.routers.counters import counters_db
    
    if skill_id not in skills_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skill with id {skill_id} not found"
        )
    
    skill = skills_db[skill_id]
    
    # Get descendants
    skill_parent_map = {sid: s.parent_id for sid, s in skills_db.items()}
    descendants = get_descendants(skill_id, skill_parent_map)
    
    # Get direct children
    direct_children = [s for s in skills_db.values() if s.parent_id == skill_id]
    
    # Aggregate counters from this skill and all descendants
    counter_aggregation: Dict[tuple, Dict] = {}  # Key: (name, unit), Value: {total, count, target}
    
    # Include this skill and all descendants
    skill_ids_to_aggregate = {skill_id} | descendants
    
    for sid in skill_ids_to_aggregate:
        skill_counters = [c for c in counters_db.values() if c.skill_id == sid]
        for counter in skill_counters:
            key = (counter.name, counter.unit or "")
            if key not in counter_aggregation:
                counter_aggregation[key] = {"total": 0.0, "count": 0, "target": 0.0}
            counter_aggregation[key]["total"] += counter.value
            counter_aggregation[key]["count"] += 1
            # Aggregate targets - sum up all target values
            if counter.target is not None:
                counter_aggregation[key]["target"] += counter.target
    
    # Build counter summaries
    counter_totals = [
        CounterSummary(
            name=name,
            unit=unit if unit else None,
            total=data["total"],
            target=data["target"] if data["target"] > 0 else None,
            count=data["count"]
        )
        for (name, unit), data in counter_aggregation.items()
    ]
    
    # Build child summaries recursively
    children_summaries = [get_skill_summary(child.id) for child in direct_children]
    
    return SkillSummary(
        id=skill.id,
        name=skill.name,
        parent_id=skill.parent_id,
        counter_totals=counter_totals,
        total_descendants=len(descendants),
        direct_children_count=len(direct_children),
        children=children_summaries
    )

