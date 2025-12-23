"""Skill model definition for hierarchical skill tree."""
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class SkillBase(BaseModel):
    """Base Skill schema with common attributes."""
    name: str = Field(..., min_length=1, max_length=255, description="Skill name")
    parent_id: Optional[int] = Field(None, description="Parent skill ID (None for root skills)")


class SkillCreate(SkillBase):
    """Schema for creating a new skill."""
    pass


class SkillUpdate(BaseModel):
    """Schema for updating an existing skill."""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Skill name")
    parent_id: Optional[int] = Field(None, description="Parent skill ID (use -1 to set as root skill)")


class Skill(SkillBase):
    """Complete Skill model with all attributes."""
    id: int = Field(..., description="Unique skill identifier")

    model_config = ConfigDict(from_attributes=True)


class SkillWithChildren(Skill):
    """Skill model with nested children for tree representation."""
    children: list["SkillWithChildren"] = Field(default_factory=list, description="Child skills")

    model_config = ConfigDict(from_attributes=True)


# Required for forward reference resolution
SkillWithChildren.model_rebuild()
