"""Counter model definition for tracking skill metrics."""
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class CounterBase(BaseModel):
    """Base Counter schema with common attributes."""
    name: str = Field(..., min_length=1, max_length=255, description="Counter name (e.g., 'Hours Practiced', 'Exercises Completed')")
    unit: Optional[str] = Field(None, max_length=50, description="Unit of measurement (e.g., 'hours', 'exercises', 'pages')")
    value: float = Field(default=0.0, ge=0, description="Current counter value (must be non-negative)")
    target: Optional[float] = Field(None, ge=0, description="Optional target value for the counter")


class CounterCreate(BaseModel):
    """Schema for creating a new counter."""
    name: str = Field(..., min_length=1, max_length=255, description="Counter name")
    unit: Optional[str] = Field(None, max_length=50, description="Unit of measurement")
    value: float = Field(default=0.0, ge=0, description="Initial counter value")
    target: Optional[float] = Field(None, ge=0, description="Optional target value")


class CounterUpdate(BaseModel):
    """Schema for updating an existing counter."""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Counter name")
    unit: Optional[str] = Field(None, max_length=50, description="Unit of measurement")
    value: Optional[float] = Field(None, ge=0, description="Counter value")
    target: Optional[float] = Field(None, ge=0, description="Target value")


class Counter(CounterBase):
    """Complete Counter model with all attributes."""
    id: int = Field(..., description="Unique counter identifier")
    skill_id: int = Field(..., description="ID of the skill this counter belongs to")

    model_config = ConfigDict(from_attributes=True)
