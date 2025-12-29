"""Skill model definition for hierarchical skill tree."""
from typing import Optional, List
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


class CounterSummary(BaseModel):
    """Summary of counter values."""
    name: str = Field(..., description="Counter name")
    unit: Optional[str] = Field(None, description="Counter unit")
    total: float = Field(..., description="Total counter value")
    count: int = Field(..., description="Number of counters aggregated")


class SkillSummary(Skill):
    """Skill with aggregated counter summaries and child information."""
    counter_totals: List[CounterSummary] = Field(default_factory=list, description="Aggregated counter values")
    total_descendants: int = Field(0, description="Total number of descendants")
    direct_children_count: int = Field(0, description="Number of direct children")
    children: List["SkillSummary"] = Field(default_factory=list, description="Child skill summaries")

    model_config = ConfigDict(from_attributes=True)


# Required for forward reference resolution
SkillSummary.model_rebuild()
