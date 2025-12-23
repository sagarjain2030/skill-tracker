"""Validation utilities for skill hierarchy."""
from typing import Dict, Optional, Set


class CyclicDependencyError(ValueError):
    """Raised when a cyclic dependency is detected in skill hierarchy."""
    pass


def validate_no_cycle(
    skill_id: int,
    new_parent_id: Optional[int],
    skill_parent_map: Dict[int, Optional[int]]
) -> None:
    """
    Validate that setting a skill's parent does not create a cycle.
    
    A cycle occurs when a skill becomes its own ancestor.
    
    Args:
        skill_id: The ID of the skill being updated
        new_parent_id: The proposed new parent ID (None for root)
        skill_parent_map: Dictionary mapping skill IDs to their parent IDs
        
    Raises:
        CyclicDependencyError: If the operation would create a cycle
        
    Examples:
        >>> # Valid: setting a parent for a root skill
        >>> validate_no_cycle(2, 1, {1: None, 2: None})
        
        >>> # Invalid: skill cannot be its own parent
        >>> validate_no_cycle(1, 1, {1: None})
        Traceback (most recent call last):
        ...
        CyclicDependencyError: Skill cannot be its own parent
        
        >>> # Invalid: creating a cycle (1 -> 2 -> 1)
        >>> validate_no_cycle(1, 2, {1: None, 2: 1})
        Traceback (most recent call last):
        ...
        CyclicDependencyError: Setting parent would create a cycle: skill 1 is an ancestor of skill 2
    """
    # If parent is None, it's a root skill - no cycle possible
    if new_parent_id is None:
        return
    
    # A skill cannot be its own parent
    if skill_id == new_parent_id:
        raise CyclicDependencyError("Skill cannot be its own parent")
    
    # Check if the proposed parent is a descendant of this skill
    # by traversing up from the parent
    visited: Set[int] = set()
    current = new_parent_id
    
    while current is not None:
        # If we encounter the skill being updated, we found a cycle
        if current == skill_id:
            raise CyclicDependencyError(
                f"Setting parent would create a cycle: "
                f"skill {skill_id} is an ancestor of skill {new_parent_id}"
            )
        
        # Detect infinite loop (shouldn't happen with valid data)
        if current in visited:
            raise CyclicDependencyError(
                f"Existing cycle detected in skill tree at skill {current}"
            )
        
        visited.add(current)
        
        # Move to parent
        current = skill_parent_map.get(current)


def get_ancestors(
    skill_id: int,
    skill_parent_map: Dict[int, Optional[int]]
) -> Set[int]:
    """
    Get all ancestor IDs of a skill.
    
    Args:
        skill_id: The skill ID to get ancestors for
        skill_parent_map: Dictionary mapping skill IDs to their parent IDs
        
    Returns:
        Set of ancestor skill IDs (not including the skill itself)
        
    Examples:
        >>> # Root skill has no ancestors
        >>> get_ancestors(1, {1: None})
        set()
        
        >>> # Child skill has one ancestor
        >>> get_ancestors(2, {1: None, 2: 1})
        {1}
        
        >>> # Grandchild has two ancestors
        >>> get_ancestors(3, {1: None, 2: 1, 3: 2})
        {1, 2}
    """
    ancestors: Set[int] = set()
    current = skill_parent_map.get(skill_id)
    
    while current is not None:
        ancestors.add(current)
        current = skill_parent_map.get(current)
    
    return ancestors


def get_descendants(
    skill_id: int,
    skill_parent_map: Dict[int, Optional[int]]
) -> Set[int]:
    """
    Get all descendant IDs of a skill.
    
    Args:
        skill_id: The skill ID to get descendants for
        skill_parent_map: Dictionary mapping skill IDs to their parent IDs
        
    Returns:
        Set of descendant skill IDs (not including the skill itself)
        
    Examples:
        >>> # Leaf skill has no descendants
        >>> get_descendants(3, {1: None, 2: 1, 3: 2})
        set()
        
        >>> # Parent has one descendant
        >>> get_descendants(2, {1: None, 2: 1, 3: 2})
        {3}
        
        >>> # Root has all skills as descendants
        >>> get_descendants(1, {1: None, 2: 1, 3: 2})
        {2, 3}
    """
    descendants: Set[int] = set()
    
    # Find all skills that have this skill as an ancestor
    for child_id, parent_id in skill_parent_map.items():
        if parent_id == skill_id:
            descendants.add(child_id)
            # Recursively get descendants of children
            descendants.update(get_descendants(child_id, skill_parent_map))
    
    return descendants
