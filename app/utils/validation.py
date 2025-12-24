"""Validation utilities for skill hierarchy."""
from typing import Dict, Optional, Set, List
from collections import deque


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


def traverse_dfs(
    skill_id: int,
    skill_parent_map: Dict[int, Optional[int]]
) -> List[int]:
    """
    Perform depth-first search (DFS) traversal starting from a skill.
    
    Visits the skill, then recursively visits all its children in depth-first order.
    This means going as deep as possible down one branch before backtracking.
    
    Args:
        skill_id: The skill ID to start traversal from
        skill_parent_map: Dictionary mapping skill IDs to their parent IDs
        
    Returns:
        List of skill IDs in DFS order (includes the starting skill)
        
    Examples:
        >>> # Single skill
        >>> traverse_dfs(1, {1: None})
        [1]
        
        >>> # Linear hierarchy: 1 -> 2 -> 3
        >>> traverse_dfs(1, {1: None, 2: 1, 3: 2})
        [1, 2, 3]
        
        >>> # Tree: 1 -> (2, 3), 2 -> 4
        >>> result = traverse_dfs(1, {1: None, 2: 1, 3: 1, 4: 2})
        >>> result[0]  # Always starts with root
        1
        >>> len(result)  # Contains all nodes
        4
    """
    result: List[int] = []
    
    def _dfs_helper(current_id: int) -> None:
        """Recursively perform DFS."""
        # Visit current node
        result.append(current_id)
        
        # Find and visit all children
        children = [
            child_id for child_id, parent_id in skill_parent_map.items()
            if parent_id == current_id
        ]
        
        # Sort children by ID for deterministic ordering
        children.sort()
        
        for child_id in children:
            _dfs_helper(child_id)
    
    _dfs_helper(skill_id)
    return result


def traverse_bfs(
    skill_id: int,
    skill_parent_map: Dict[int, Optional[int]]
) -> List[int]:
    """
    Perform breadth-first search (BFS) traversal starting from a skill.
    
    Visits the skill, then visits all its immediate children, then all grandchildren,
    and so on level by level. This means visiting all nodes at depth N before any at depth N+1.
    
    Args:
        skill_id: The skill ID to start traversal from
        skill_parent_map: Dictionary mapping skill IDs to their parent IDs
        
    Returns:
        List of skill IDs in BFS order (includes the starting skill)
        
    Examples:
        >>> # Single skill
        >>> traverse_bfs(1, {1: None})
        [1]
        
        >>> # Linear hierarchy: 1 -> 2 -> 3
        >>> traverse_bfs(1, {1: None, 2: 1, 3: 2})
        [1, 2, 3]
        
        >>> # Tree: 1 -> (2, 3), 2 -> 4
        >>> result = traverse_bfs(1, {1: None, 2: 1, 3: 1, 4: 2})
        >>> result[0]  # Always starts with root
        1
        >>> result[1:3]  # Next level (children of 1)
        [2, 3]
        >>> result[3]  # Last level (child of 2)
        4
    """
    result: List[int] = []
    queue: deque = deque([skill_id])
    
    while queue:
        current_id = queue.popleft()
        result.append(current_id)
        
        # Find all children of current node
        children = [
            child_id for child_id, parent_id in skill_parent_map.items()
            if parent_id == current_id
        ]
        
        # Sort children by ID for deterministic ordering
        children.sort()
        
        # Add children to queue for processing
        queue.extend(children)
    
    return result
