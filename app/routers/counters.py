"""Counters API router."""
from typing import Dict, List
from fastapi import APIRouter, HTTPException, status
from app.models.counter import Counter, CounterCreate, CounterUpdate

router = APIRouter(prefix="/counters", tags=["Counters"])

# In-memory storage for counters (will be replaced with database later)
counters_db: Dict[int, Counter] = {}
next_counter_id = 1


@router.post("/", response_model=Counter, status_code=status.HTTP_201_CREATED)
def create_counter(skill_id: int, counter_data: CounterCreate) -> Counter:
    """
    Create a new counter for a skill.
    
    Counters track metrics like hours practiced, exercises completed, etc.
    Each counter belongs to a specific skill.
    
    Args:
        skill_id: The ID of the skill to create the counter for
        counter_data: The counter creation data
        
    Returns:
        The created counter
        
    Raises:
        HTTPException 404: If skill not found
    """
    global next_counter_id
    
    # Import here to avoid circular dependency
    from app.routers.skills import skills_db
    
    # Validate skill exists
    if skill_id not in skills_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skill with id {skill_id} not found"
        )
    
    # Create the counter
    counter = Counter(
        id=next_counter_id,
        skill_id=skill_id,
        name=counter_data.name,
        unit=counter_data.unit,
        value=counter_data.value,
        target=counter_data.target
    )
    
    counters_db[next_counter_id] = counter
    next_counter_id += 1
    
    return counter


@router.get("/", response_model=List[Counter])
def list_counters(skill_id: int | None = None) -> List[Counter]:
    """
    List all counters, optionally filtered by skill.
    
    Args:
        skill_id: Optional skill ID to filter counters by
        
    Returns:
        List of counters (all or filtered by skill)
    """
    if skill_id is None:
        return list(counters_db.values())
    
    return [counter for counter in counters_db.values() if counter.skill_id == skill_id]


@router.get("/{counter_id}", response_model=Counter)
def get_counter(counter_id: int) -> Counter:
    """
    Get a counter by ID.
    
    Args:
        counter_id: The counter ID
        
    Returns:
        The counter
        
    Raises:
        HTTPException 404: If counter not found
    """
    if counter_id not in counters_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Counter with id {counter_id} not found"
        )
    
    return counters_db[counter_id]


@router.patch("/{counter_id}", response_model=Counter)
def update_counter(counter_id: int, counter_data: CounterUpdate) -> Counter:
    """
    Update an existing counter.
    
    Can update name, unit, value, and/or target.
    Only provided fields will be updated.
    
    Args:
        counter_id: The ID of the counter to update
        counter_data: The update data
        
    Returns:
        The updated counter
        
    Raises:
        HTTPException 404: If counter not found
    """
    # Check counter exists
    if counter_id not in counters_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Counter with id {counter_id} not found"
        )
    
    existing_counter = counters_db[counter_id]
    
    # Update counter with provided fields
    update_data = counter_data.model_dump(exclude_unset=True)
    updated_counter = Counter(
        id=existing_counter.id,
        skill_id=existing_counter.skill_id,
        name=update_data.get("name", existing_counter.name),
        unit=update_data.get("unit", existing_counter.unit),
        value=update_data.get("value", existing_counter.value),
        target=update_data.get("target", existing_counter.target)
    )
    
    counters_db[counter_id] = updated_counter
    return updated_counter


@router.delete("/{counter_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_counter(counter_id: int) -> None:
    """
    Delete a counter.
    
    Args:
        counter_id: The ID of the counter to delete
        
    Returns:
        None (204 No Content on success)
        
    Raises:
        HTTPException 404: If counter not found
    """
    # Check counter exists
    if counter_id not in counters_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Counter with id {counter_id} not found"
        )
    
    # Delete the counter
    del counters_db[counter_id]
    return None


@router.post("/{counter_id}/increment", response_model=Counter)
def increment_counter(counter_id: int, amount: float = 1.0) -> Counter:
    """
    Increment a counter's value by a specified amount.
    
    Convenience endpoint for adding to a counter without needing to
    know its current value.
    
    Args:
        counter_id: The ID of the counter to increment
        amount: The amount to add (default: 1.0)
        
    Returns:
        The updated counter
        
    Raises:
        HTTPException 404: If counter not found
        HTTPException 400: If amount would make value negative
    """
    # Check counter exists
    if counter_id not in counters_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Counter with id {counter_id} not found"
        )
    
    existing_counter = counters_db[counter_id]
    new_value = existing_counter.value + amount
    
    # Validate new value is non-negative
    if new_value < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot increment by {amount}: would result in negative value"
        )
    
    # Update counter
    updated_counter = Counter(
        id=existing_counter.id,
        skill_id=existing_counter.skill_id,
        name=existing_counter.name,
        unit=existing_counter.unit,
        value=new_value,
        target=existing_counter.target
    )
    
    counters_db[counter_id] = updated_counter
    return updated_counter
