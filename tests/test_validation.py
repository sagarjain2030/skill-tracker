"""Tests for skill hierarchy validation utilities."""
import pytest
from app.utils.validation import (
    CyclicDependencyError,
    validate_no_cycle,
    get_ancestors,
    get_descendants,
    traverse_dfs,
    traverse_bfs,
)


class TestValidateNoCycle:
    """Tests for cycle detection in skill hierarchy."""

    def test_root_skill_no_cycle(self):
        """Test that root skills (parent=None) cannot create cycles."""
        skill_parent_map = {1: None, 2: None, 3: None}
        # Setting parent to None is always valid
        validate_no_cycle(1, None, skill_parent_map)
        validate_no_cycle(2, None, skill_parent_map)

    def test_simple_parent_child_valid(self):
        """Test valid simple parent-child relationship."""
        skill_parent_map = {1: None, 2: None}
        # Setting skill 2's parent to skill 1 is valid
        validate_no_cycle(2, 1, skill_parent_map)

    def test_skill_cannot_be_own_parent(self):
        """Test that a skill cannot be its own parent."""
        skill_parent_map = {1: None}
        with pytest.raises(CyclicDependencyError) as exc_info:
            validate_no_cycle(1, 1, skill_parent_map)
        assert "cannot be its own parent" in str(exc_info.value)

    def test_direct_cycle_detection(self):
        """Test detection of direct cycle (A -> B, B -> A)."""
        # Current state: 1 -> None, 2 -> 1
        skill_parent_map = {1: None, 2: 1}
        
        # Trying to set skill 1's parent to skill 2 creates a cycle
        with pytest.raises(CyclicDependencyError) as exc_info:
            validate_no_cycle(1, 2, skill_parent_map)
        assert "create a cycle" in str(exc_info.value)
        assert "skill 1 is an ancestor of skill 2" in str(exc_info.value)

    def test_indirect_cycle_detection(self):
        """Test detection of indirect cycle (A -> B -> C, C -> A)."""
        # Current state: 1 -> None, 2 -> 1, 3 -> 2
        skill_parent_map = {1: None, 2: 1, 3: 2}
        
        # Trying to set skill 1's parent to skill 3 creates a cycle
        with pytest.raises(CyclicDependencyError) as exc_info:
            validate_no_cycle(1, 3, skill_parent_map)
        assert "create a cycle" in str(exc_info.value)

    def test_deep_cycle_detection(self):
        """Test detection of cycle in deep hierarchy."""
        # Build a deep tree: 1 -> 2 -> 3 -> 4 -> 5
        skill_parent_map = {
            1: None,
            2: 1,
            3: 2,
            4: 3,
            5: 4,
        }
        
        # Trying to set skill 1's parent to skill 5 creates a cycle
        with pytest.raises(CyclicDependencyError) as exc_info:
            validate_no_cycle(1, 5, skill_parent_map)
        assert "create a cycle" in str(exc_info.value)

    def test_valid_sibling_relationship(self):
        """Test that siblings can be reparented to each other."""
        # Current state: 1 -> None, 2 -> 1, 3 -> 1 (2 and 3 are siblings)
        skill_parent_map = {1: None, 2: 1, 3: 1}
        
        # Setting skill 3's parent to skill 2 is valid (no cycle)
        validate_no_cycle(3, 2, skill_parent_map)

    def test_reparenting_to_descendant_not_allowed(self):
        """Test that a skill cannot be reparented to its descendant."""
        # Current state: 1 -> None, 2 -> 1, 3 -> 2, 4 -> 3
        skill_parent_map = {1: None, 2: 1, 3: 2, 4: 3}
        
        # Skill 2 cannot be reparented to skill 4 (its descendant)
        with pytest.raises(CyclicDependencyError):
            validate_no_cycle(2, 4, skill_parent_map)

    def test_moving_subtree_valid(self):
        """Test that moving an entire subtree is valid if no cycle."""
        # Current state: 1 -> None, 2 -> 1, 3 -> 2, 4 -> None, 5 -> 4
        skill_parent_map = {1: None, 2: 1, 3: 2, 4: None, 5: 4}
        
        # Moving subtree rooted at 4 under skill 1 is valid
        validate_no_cycle(4, 1, skill_parent_map)
        
        # Moving subtree rooted at 4 under skill 2 is valid
        validate_no_cycle(4, 2, skill_parent_map)


class TestGetAncestors:
    """Tests for getting ancestor skills."""

    def test_root_has_no_ancestors(self):
        """Test that root skills have no ancestors."""
        skill_parent_map = {1: None}
        ancestors = get_ancestors(1, skill_parent_map)
        assert ancestors == set()

    def test_child_has_one_ancestor(self):
        """Test that direct child has one ancestor."""
        skill_parent_map = {1: None, 2: 1}
        ancestors = get_ancestors(2, skill_parent_map)
        assert ancestors == {1}

    def test_grandchild_has_two_ancestors(self):
        """Test that grandchild has two ancestors."""
        skill_parent_map = {1: None, 2: 1, 3: 2}
        ancestors = get_ancestors(3, skill_parent_map)
        assert ancestors == {1, 2}

    def test_deep_hierarchy_ancestors(self):
        """Test ancestors in deep hierarchy."""
        skill_parent_map = {1: None, 2: 1, 3: 2, 4: 3, 5: 4}
        ancestors = get_ancestors(5, skill_parent_map)
        assert ancestors == {1, 2, 3, 4}

    def test_nonexistent_skill_no_ancestors(self):
        """Test that nonexistent skill has no ancestors."""
        skill_parent_map = {1: None, 2: 1}
        ancestors = get_ancestors(999, skill_parent_map)
        assert ancestors == set()


class TestGetDescendants:
    """Tests for getting descendant skills."""

    def test_leaf_has_no_descendants(self):
        """Test that leaf skills have no descendants."""
        skill_parent_map = {1: None, 2: 1, 3: 2}
        descendants = get_descendants(3, skill_parent_map)
        assert descendants == set()

    def test_parent_has_one_descendant(self):
        """Test that parent with one child has one descendant."""
        skill_parent_map = {1: None, 2: 1}
        descendants = get_descendants(1, skill_parent_map)
        assert descendants == {2}

    def test_parent_has_multiple_direct_descendants(self):
        """Test parent with multiple children."""
        skill_parent_map = {1: None, 2: 1, 3: 1, 4: 1}
        descendants = get_descendants(1, skill_parent_map)
        assert descendants == {2, 3, 4}

    def test_root_has_all_descendants(self):
        """Test that root skill has all other skills as descendants."""
        skill_parent_map = {1: None, 2: 1, 3: 2, 4: 1, 5: 4}
        descendants = get_descendants(1, skill_parent_map)
        assert descendants == {2, 3, 4, 5}

    def test_middle_node_descendants(self):
        """Test descendants of middle node in hierarchy."""
        skill_parent_map = {1: None, 2: 1, 3: 2, 4: 2, 5: 3}
        # Skill 2's descendants are 3, 4, and 5 (where 5 is grandchild)
        descendants = get_descendants(2, skill_parent_map)
        assert descendants == {3, 4, 5}

    def test_multiple_subtrees(self):
        """Test descendants with multiple independent subtrees."""
        skill_parent_map = {
            1: None,  # Root 1
            2: 1,     # Child of 1
            3: 1,     # Child of 1
            4: None,  # Root 2 (separate tree)
            5: 4,     # Child of 4
        }
        
        # Root 1's descendants
        descendants_1 = get_descendants(1, skill_parent_map)
        assert descendants_1 == {2, 3}
        
        # Root 2's descendants
        descendants_4 = get_descendants(4, skill_parent_map)
        assert descendants_4 == {5}


class TestCyclicDependencyIntegration:
    """Integration tests for cyclic dependency prevention."""

    def test_complex_tree_operations(self):
        """Test various operations on a complex tree structure."""
        # Build a complex tree:
        #       1
        #      / \
        #     2   3
        #    /     \
        #   4       5
        #          / \
        #         6   7
        
        skill_parent_map = {
            1: None,
            2: 1,
            3: 1,
            4: 2,
            5: 3,
            6: 5,
            7: 5,
        }
        
        # Valid: Move leaf 6 to be child of 2
        validate_no_cycle(6, 2, skill_parent_map)
        
        # Valid: Move subtree 5 (with 6,7) to be child of 2
        validate_no_cycle(5, 2, skill_parent_map)
        
        # Invalid: Move 1 to be child of 5 (cycle)
        with pytest.raises(CyclicDependencyError):
            validate_no_cycle(1, 5, skill_parent_map)
        
        # Invalid: Move 3 to be child of 5 (cycle)
        with pytest.raises(CyclicDependencyError):
            validate_no_cycle(3, 5, skill_parent_map)
        
        # Valid: Move 7 to root level
        validate_no_cycle(7, None, skill_parent_map)

    def test_prevent_self_ancestry(self):
        """Test that skills cannot become their own ancestors through any path."""
        skill_parent_map = {1: None, 2: 1, 3: 2, 4: 3}
        
        # All these would make the skill its own ancestor
        with pytest.raises(CyclicDependencyError):
            validate_no_cycle(1, 2, skill_parent_map)
        
        with pytest.raises(CyclicDependencyError):
            validate_no_cycle(1, 3, skill_parent_map)
        
        with pytest.raises(CyclicDependencyError):
            validate_no_cycle(1, 4, skill_parent_map)
        
        with pytest.raises(CyclicDependencyError):
            validate_no_cycle(2, 3, skill_parent_map)
        
        with pytest.raises(CyclicDependencyError):
            validate_no_cycle(2, 4, skill_parent_map)


class TestTraverseDFS:
    """Tests for depth-first search traversal."""

    def test_dfs_single_node(self):
        """Test DFS on a single node."""
        skill_parent_map = {1: None}
        result = traverse_dfs(1, skill_parent_map)
        assert result == [1]

    def test_dfs_linear_hierarchy(self):
        """Test DFS on linear hierarchy: 1 -> 2 -> 3."""
        skill_parent_map = {1: None, 2: 1, 3: 2}
        result = traverse_dfs(1, skill_parent_map)
        # DFS on linear tree: visits in order
        assert result == [1, 2, 3]

    def test_dfs_with_siblings(self):
        """Test DFS with multiple children at same level."""
        # Tree: 1 -> (2, 3)
        skill_parent_map = {1: None, 2: 1, 3: 1}
        result = traverse_dfs(1, skill_parent_map)
        # Should visit root, then all children
        assert result[0] == 1
        assert set(result[1:]) == {2, 3}
        assert len(result) == 3

    def test_dfs_complex_tree(self):
        """Test DFS on complex tree structure."""
        # Tree:     1
        #          / \
        #         2   3
        #        /
        #       4
        skill_parent_map = {1: None, 2: 1, 3: 1, 4: 2}
        result = traverse_dfs(1, skill_parent_map)
        
        # Root is first
        assert result[0] == 1
        # All nodes are visited
        assert set(result) == {1, 2, 3, 4}
        assert len(result) == 4
        # DFS property: if we visit 2, we must visit 4 before 3
        idx_2 = result.index(2)
        idx_3 = result.index(3)
        idx_4 = result.index(4)
        # 4 should come after 2 but before 3 (going deep first)
        assert idx_2 < idx_4 < idx_3

    def test_dfs_subtree(self):
        """Test DFS starting from non-root node."""
        # Tree:     1
        #          / \
        #         2   5
        #        / \
        #       3   4
        skill_parent_map = {1: None, 2: 1, 3: 2, 4: 2, 5: 1}
        result = traverse_dfs(2, skill_parent_map)
        
        # Should only include node 2 and its descendants
        assert set(result) == {2, 3, 4}
        assert result[0] == 2
        # Should not include nodes 1 or 5
        assert 1 not in result
        assert 5 not in result

    def test_dfs_deep_hierarchy(self):
        """Test DFS on deep linear hierarchy."""
        # 1 -> 2 -> 3 -> 4 -> 5
        skill_parent_map = {1: None, 2: 1, 3: 2, 4: 3, 5: 4}
        result = traverse_dfs(1, skill_parent_map)
        # Linear structure should be visited in order
        assert result == [1, 2, 3, 4, 5]

    def test_dfs_multiple_branches(self):
        """Test DFS with multiple branches."""
        # Tree:       1
        #          /  |  \
        #         2   3   4
        #        /        |
        #       5         6
        skill_parent_map = {1: None, 2: 1, 3: 1, 4: 1, 5: 2, 6: 4}
        result = traverse_dfs(1, skill_parent_map)
        
        assert result[0] == 1
        assert set(result) == {1, 2, 3, 4, 5, 6}
        # DFS visits branch completely before moving to next
        idx_2 = result.index(2)
        idx_5 = result.index(5)
        idx_3 = result.index(3)
        # 5 should come right after 2, before 3
        assert idx_2 < idx_5 < idx_3


class TestTraverseBFS:
    """Tests for breadth-first search traversal."""

    def test_bfs_single_node(self):
        """Test BFS on a single node."""
        skill_parent_map = {1: None}
        result = traverse_bfs(1, skill_parent_map)
        assert result == [1]

    def test_bfs_linear_hierarchy(self):
        """Test BFS on linear hierarchy: 1 -> 2 -> 3."""
        skill_parent_map = {1: None, 2: 1, 3: 2}
        result = traverse_bfs(1, skill_parent_map)
        # BFS on linear tree: visits in order (same as DFS for linear)
        assert result == [1, 2, 3]

    def test_bfs_with_siblings(self):
        """Test BFS with multiple children at same level."""
        # Tree: 1 -> (2, 3)
        skill_parent_map = {1: None, 2: 1, 3: 1}
        result = traverse_bfs(1, skill_parent_map)
        # Should visit root, then all children at same level
        assert result[0] == 1
        assert set(result[1:]) == {2, 3}
        assert len(result) == 3

    def test_bfs_complex_tree(self):
        """Test BFS on complex tree structure."""
        # Tree:     1
        #          / \
        #         2   3
        #        /
        #       4
        skill_parent_map = {1: None, 2: 1, 3: 1, 4: 2}
        result = traverse_bfs(1, skill_parent_map)
        
        # Root is first
        assert result[0] == 1
        # Level 1 (children of root) comes before level 2
        assert result[1:3] == [2, 3] or result[1:3] == [3, 2]
        # Level 2 (grandchildren) comes last
        assert result[3] == 4
        # All nodes visited
        assert set(result) == {1, 2, 3, 4}

    def test_bfs_level_order(self):
        """Test BFS visits nodes level by level."""
        # Tree:       1
        #          /  |  \
        #         2   3   4
        #        /        |
        #       5         6
        skill_parent_map = {1: None, 2: 1, 3: 1, 4: 1, 5: 2, 6: 4}
        result = traverse_bfs(1, skill_parent_map)
        
        # Level 0: node 1
        assert result[0] == 1
        # Level 1: nodes 2, 3, 4 (all children of 1)
        level1 = result[1:4]
        assert set(level1) == {2, 3, 4}
        # Level 2: nodes 5, 6 (grandchildren of 1)
        level2 = result[4:6]
        assert set(level2) == {5, 6}
        # All nodes visited
        assert len(result) == 6

    def test_bfs_subtree(self):
        """Test BFS starting from non-root node."""
        # Tree:     1
        #          / \
        #         2   5
        #        / \
        #       3   4
        skill_parent_map = {1: None, 2: 1, 3: 2, 4: 2, 5: 1}
        result = traverse_bfs(2, skill_parent_map)
        
        # Should only include node 2 and its descendants
        assert result[0] == 2
        assert set(result) == {2, 3, 4}
        # Should not include nodes 1 or 5
        assert 1 not in result
        assert 5 not in result

    def test_bfs_deep_hierarchy(self):
        """Test BFS on deep linear hierarchy."""
        # 1 -> 2 -> 3 -> 4 -> 5
        skill_parent_map = {1: None, 2: 1, 3: 2, 4: 3, 5: 4}
        result = traverse_bfs(1, skill_parent_map)
        # Linear structure: BFS and DFS give same result
        assert result == [1, 2, 3, 4, 5]

    def test_bfs_vs_dfs_difference(self):
        """Test that BFS differs from DFS on branching tree."""
        # Tree:     1
        #          / \
        #         2   3
        #        / \
        #       4   5
        skill_parent_map = {1: None, 2: 1, 3: 1, 4: 2, 5: 2}
        
        bfs_result = traverse_bfs(1, skill_parent_map)
        dfs_result = traverse_dfs(1, skill_parent_map)
        
        # Both start with root
        assert bfs_result[0] == 1
        assert dfs_result[0] == 1
        
        # BFS: 1, then level 1 (2,3), then level 2 (4,5)
        # So 3 comes before 4 and 5
        bfs_idx_3 = bfs_result.index(3)
        bfs_idx_4 = bfs_result.index(4)
        bfs_idx_5 = bfs_result.index(5)
        assert bfs_idx_3 < bfs_idx_4
        assert bfs_idx_3 < bfs_idx_5
        
        # DFS: 1, then 2, then 2's children (4,5), then 3
        # So 3 comes after 4 and 5
        dfs_idx_3 = dfs_result.index(3)
        dfs_idx_4 = dfs_result.index(4)
        dfs_idx_5 = dfs_result.index(5)
        assert dfs_idx_3 > dfs_idx_4
        assert dfs_idx_3 > dfs_idx_5
