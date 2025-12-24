"""Tests for Counter model."""
import pytest
from pydantic import ValidationError
from app.models.counter import (
    Counter,
    CounterBase,
    CounterCreate,
    CounterUpdate,
)


class TestCounterBase:
    """Tests for CounterBase schema."""

    def test_counter_base_valid(self):
        """Test valid counter base creation."""
        counter = CounterBase(name="Hours Practiced", unit="hours", value=10.5, target=100.0)
        assert counter.name == "Hours Practiced"
        assert counter.unit == "hours"
        assert counter.value == 10.5
        assert counter.target == 100.0

    def test_counter_base_minimal(self):
        """Test counter with minimal fields (only name required)."""
        counter = CounterBase(name="Practice Sessions")
        assert counter.name == "Practice Sessions"
        assert counter.unit is None
        assert counter.value == 0.0
        assert counter.target is None

    def test_counter_base_name_required(self):
        """Test that counter name is required."""
        with pytest.raises(ValidationError):
            CounterBase()

    def test_counter_base_name_not_empty(self):
        """Test that counter name cannot be empty."""
        with pytest.raises(ValidationError):
            CounterBase(name="")

    def test_counter_base_name_max_length(self):
        """Test that counter name has max length of 255."""
        long_name = "a" * 256
        with pytest.raises(ValidationError):
            CounterBase(name=long_name)

    def test_counter_base_value_non_negative(self):
        """Test that counter value must be non-negative."""
        with pytest.raises(ValidationError):
            CounterBase(name="Test", value=-1.0)

    def test_counter_base_target_non_negative(self):
        """Test that counter target must be non-negative."""
        with pytest.raises(ValidationError):
            CounterBase(name="Test", target=-10.0)

    def test_counter_base_with_decimals(self):
        """Test counter with decimal values."""
        counter = CounterBase(name="Test", value=3.14159, target=10.5)
        assert counter.value == 3.14159
        assert counter.target == 10.5


class TestCounterCreate:
    """Tests for CounterCreate schema."""

    def test_counter_create_full(self):
        """Test creating counter with all fields."""
        counter = CounterCreate(
            name="Exercises Completed",
            unit="exercises",
            value=25.0,
            target=100.0
        )
        assert counter.name == "Exercises Completed"
        assert counter.unit == "exercises"
        assert counter.value == 25.0
        assert counter.target == 100.0

    def test_counter_create_minimal(self):
        """Test creating counter with minimal fields."""
        counter = CounterCreate(name="Test Counter")
        assert counter.name == "Test Counter"
        assert counter.value == 0.0


class TestCounterUpdate:
    """Tests for CounterUpdate schema."""

    def test_counter_update_all_fields(self):
        """Test updating all counter fields."""
        update = CounterUpdate(
            name="New Name",
            unit="new_unit",
            value=50.0,
            target=200.0
        )
        assert update.name == "New Name"
        assert update.unit == "new_unit"
        assert update.value == 50.0
        assert update.target == 200.0

    def test_counter_update_optional(self):
        """Test that all update fields are optional."""
        update = CounterUpdate()
        assert update.name is None
        assert update.unit is None
        assert update.value is None
        assert update.target is None

    def test_counter_update_partial(self):
        """Test partial counter update."""
        update = CounterUpdate(value=75.0)
        assert update.name is None
        assert update.value == 75.0
        assert update.target is None


class TestCounter:
    """Tests for complete Counter model."""

    def test_counter_complete(self):
        """Test complete counter with all fields."""
        counter = Counter(
            id=1,
            skill_id=10,
            name="Pages Read",
            unit="pages",
            value=150.0,
            target=500.0
        )
        assert counter.id == 1
        assert counter.skill_id == 10
        assert counter.name == "Pages Read"
        assert counter.unit == "pages"
        assert counter.value == 150.0
        assert counter.target == 500.0

    def test_counter_id_required(self):
        """Test that counter ID is required."""
        with pytest.raises(ValidationError):
            Counter(
                skill_id=1,
                name="Test",
                value=0.0
            )

    def test_counter_skill_id_required(self):
        """Test that skill_id is required."""
        with pytest.raises(ValidationError):
            Counter(
                id=1,
                name="Test",
                value=0.0
            )


class TestCounterScenarios:
    """Tests for real-world counter scenarios."""

    def test_time_based_counter(self):
        """Test counter for tracking time (hours, minutes)."""
        counter = Counter(
            id=1,
            skill_id=1,
            name="Practice Time",
            unit="hours",
            value=25.5,
            target=100.0
        )
        assert counter.unit == "hours"
        assert counter.value == 25.5

    def test_count_based_counter(self):
        """Test counter for tracking discrete items."""
        counter = Counter(
            id=2,
            skill_id=1,
            name="Problems Solved",
            unit="problems",
            value=45.0,
            target=500.0
        )
        assert counter.unit == "problems"
        assert counter.value == 45.0

    def test_counter_without_target(self):
        """Test counter without a target (open-ended tracking)."""
        counter = Counter(
            id=3,
            skill_id=1,
            name="Sessions",
            unit="sessions",
            value=10.0,
            target=None
        )
        assert counter.target is None

    def test_counter_without_unit(self):
        """Test counter without specific unit."""
        counter = Counter(
            id=4,
            skill_id=1,
            name="Repetitions",
            unit=None,
            value=100.0
        )
        assert counter.unit is None

    def test_zero_value_counter(self):
        """Test counter starting at zero."""
        counter = Counter(
            id=5,
            skill_id=1,
            name="New Skill",
            value=0.0
        )
        assert counter.value == 0.0

    def test_percentage_tracking(self):
        """Test using counter for percentage tracking."""
        counter = Counter(
            id=6,
            skill_id=1,
            name="Course Progress",
            unit="%",
            value=75.5,
            target=100.0
        )
        assert counter.unit == "%"
        progress_percentage = (counter.value / counter.target) * 100 if counter.target else 0
        assert progress_percentage == 75.5
