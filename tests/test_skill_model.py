"""Tests for Skill model and hierarchical structure."""
import pytest
from pydantic import ValidationError
from app.models.skill import (
    Skill,
    SkillBase,
    SkillCreate,
    SkillUpdate,
    SkillWithChildren,
)


class TestSkillBase:
    """Tests for SkillBase schema."""

    def test_skill_base_valid(self):
        """Test creating a valid SkillBase."""
        skill = SkillBase(name="Python", parent_id=None)
        assert skill.name == "Python"
        assert skill.parent_id is None

    def test_skill_base_with_parent(self):
        """Test creating a SkillBase with parent."""
        skill = SkillBase(name="FastAPI", parent_id=1)
        assert skill.name == "FastAPI"
        assert skill.parent_id == 1

    def test_skill_base_name_required(self):
        """Test that name is required."""
        with pytest.raises(ValidationError) as exc_info:
            SkillBase(parent_id=None)
        assert "name" in str(exc_info.value)

    def test_skill_base_name_not_empty(self):
        """Test that name cannot be empty."""
        with pytest.raises(ValidationError) as exc_info:
            SkillBase(name="", parent_id=None)
        assert "at least 1 character" in str(exc_info.value)

    def test_skill_base_name_max_length(self):
        """Test name maximum length validation."""
        long_name = "x" * 256
        with pytest.raises(ValidationError) as exc_info:
            SkillBase(name=long_name, parent_id=None)
        assert "at most 255 characters" in str(exc_info.value)


class TestSkillCreate:
    """Tests for SkillCreate schema."""

    def test_skill_create_root(self):
        """Test creating a root skill."""
        skill = SkillCreate(name="Programming", parent_id=None)
        assert skill.name == "Programming"
        assert skill.parent_id is None

    def test_skill_create_child(self):
        """Test creating a child skill."""
        skill = SkillCreate(name="Python", parent_id=1)
        assert skill.name == "Python"
        assert skill.parent_id == 1


class TestSkillUpdate:
    """Tests for SkillUpdate schema."""

    def test_skill_update_name(self):
        """Test updating skill name."""
        update = SkillUpdate(name="Updated Name")
        assert update.name == "Updated Name"

    def test_skill_update_optional(self):
        """Test that all fields are optional."""
        update = SkillUpdate()
        assert update.name is None

    def test_skill_update_name_validation(self):
        """Test name validation on update."""
        with pytest.raises(ValidationError):
            SkillUpdate(name="")


class TestSkill:
    """Tests for complete Skill model."""

    def test_skill_complete(self):
        """Test creating a complete Skill."""
        skill = Skill(id=1, name="Python", parent_id=None)
        assert skill.id == 1
        assert skill.name == "Python"
        assert skill.parent_id is None

    def test_skill_with_parent(self):
        """Test skill with parent relationship."""
        skill = Skill(id=2, name="Django", parent_id=1)
        assert skill.id == 2
        assert skill.name == "Django"
        assert skill.parent_id == 1

    def test_skill_id_required(self):
        """Test that id is required."""
        with pytest.raises(ValidationError) as exc_info:
            Skill(name="Python", parent_id=None)
        assert "id" in str(exc_info.value)


class TestSkillHierarchy:
    """Tests for hierarchical skill relationships."""

    def test_root_skill(self):
        """Test that root skills have no parent."""
        root = Skill(id=1, name="Programming", parent_id=None)
        assert root.parent_id is None

    def test_child_skill(self):
        """Test that child skills have a parent_id."""
        child = Skill(id=2, name="Python", parent_id=1)
        assert child.parent_id == 1

    def test_multiple_children_same_parent(self):
        """Test multiple skills can have the same parent."""
        child1 = Skill(id=2, name="Python", parent_id=1)
        child2 = Skill(id=3, name="JavaScript", parent_id=1)
        assert child1.parent_id == child2.parent_id == 1


class TestSkillWithChildren:
    """Tests for SkillWithChildren nested structure."""

    def test_skill_with_empty_children(self):
        """Test skill with no children."""
        skill = SkillWithChildren(id=1, name="Python", parent_id=None, children=[])
        assert skill.children == []

    def test_skill_with_children(self):
        """Test skill with nested children."""
        child1 = SkillWithChildren(id=2, name="Django", parent_id=1, children=[])
        child2 = SkillWithChildren(id=3, name="FastAPI", parent_id=1, children=[])
        parent = SkillWithChildren(
            id=1,
            name="Python",
            parent_id=None,
            children=[child1, child2]
        )
        
        assert len(parent.children) == 2
        assert parent.children[0].name == "Django"
        assert parent.children[1].name == "FastAPI"
        assert parent.children[0].parent_id == 1
        assert parent.children[1].parent_id == 1

    def test_deep_nested_tree(self):
        """Test deeply nested skill tree structure."""
        # Level 3
        grandchild = SkillWithChildren(id=3, name="REST API", parent_id=2, children=[])
        
        # Level 2
        child = SkillWithChildren(id=2, name="FastAPI", parent_id=1, children=[grandchild])
        
        # Level 1 (root)
        root = SkillWithChildren(id=1, name="Python", parent_id=None, children=[child])
        
        assert root.name == "Python"
        assert len(root.children) == 1
        assert root.children[0].name == "FastAPI"
        assert len(root.children[0].children) == 1
        assert root.children[0].children[0].name == "REST API"

    def test_skill_with_children_default_empty_list(self):
        """Test that children defaults to empty list."""
        skill = SkillWithChildren(id=1, name="Python", parent_id=None)
        assert skill.children == []
        assert isinstance(skill.children, list)
