"""Tests for Counters API."""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.routers.counters import counters_db
from app.routers.skills import skills_db
import app.routers.counters as counters_module
import app.routers.skills as skills_module

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_databases():
    """Reset both skills and counters databases before each test."""
    skills_db.clear()
    counters_db.clear()
    skills_module.next_skill_id = 1
    counters_module.next_counter_id = 1
    yield
    skills_db.clear()
    counters_db.clear()


def create_test_skill(name="Test Skill"):
    """Helper to create a skill for testing."""
    response = client.post("/api/skills/", json={"name": name})
    return response.json()["id"]


class TestCreateCounter:
    """Tests for POST /counters endpoint."""

    def test_create_counter_success(self):
        """Test successfully creating a counter."""
        skill_id = create_test_skill()
        
        response = client.post(
            f"/api/counters/?skill_id={skill_id}",
            json={
                "name": "Hours Practiced",
                "unit": "hours",
                "value": 0.0,
                "target": 100.0
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["id"] == 1
        assert data["skill_id"] == skill_id
        assert data["name"] == "Hours Practiced"
        assert data["unit"] == "hours"
        assert data["value"] == 0.0
        assert data["target"] == 100.0

    def test_create_counter_minimal(self):
        """Test creating counter with minimal data."""
        skill_id = create_test_skill()
        
        response = client.post(
            f"/api/counters/?skill_id={skill_id}",
            json={"name": "Practice Sessions"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Practice Sessions"
        assert data["value"] == 0.0
        assert data["unit"] is None
        assert data["target"] is None

    def test_create_multiple_counters_same_skill(self):
        """Test creating multiple counters for the same skill."""
        skill_id = create_test_skill()
        
        counter1 = client.post(
            f"/api/counters/?skill_id={skill_id}",
            json={"name": "Hours", "unit": "hours"}
        )
        counter2 = client.post(
            f"/api/counters/?skill_id={skill_id}",
            json={"name": "Exercises", "unit": "exercises"}
        )
        
        assert counter1.status_code == 201
        assert counter2.status_code == 201
        assert counter1.json()["id"] != counter2.json()["id"]
        assert counter1.json()["skill_id"] == skill_id
        assert counter2.json()["skill_id"] == skill_id

    def test_create_counter_skill_not_found(self):
        """Test creating counter for non-existent skill."""
        response = client.post(
            "/api/counters/?skill_id=999",
            json={"name": "Test Counter"}
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_create_counter_name_required(self):
        """Test that counter name is required."""
        skill_id = create_test_skill()
        
        response = client.post(
            f"/api/counters/?skill_id={skill_id}",
            json={}
        )
        
        assert response.status_code == 422

    def test_create_counter_negative_value_rejected(self):
        """Test that negative values are rejected."""
        skill_id = create_test_skill()
        
        response = client.post(
            f"/api/counters/?skill_id={skill_id}",
            json={"name": "Test", "value": -5.0}
        )
        
        assert response.status_code == 422


class TestListCounters:
    """Tests for GET /counters endpoint."""

    def test_list_empty_counters(self):
        """Test listing counters when none exist."""
        response = client.get("/api/counters/")
        
        assert response.status_code == 200
        assert response.json() == []

    def test_list_all_counters(self):
        """Test listing all counters."""
        skill1_id = create_test_skill("Skill 1")
        skill2_id = create_test_skill("Skill 2")
        
        client.post(f"/api/counters/?skill_id={skill1_id}", json={"name": "Counter 1"})
        client.post(f"/api/counters/?skill_id={skill2_id}", json={"name": "Counter 2"})
        
        response = client.get("/api/counters/")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_list_counters_filtered_by_skill(self):
        """Test listing counters filtered by skill."""
        skill1_id = create_test_skill("Skill 1")
        skill2_id = create_test_skill("Skill 2")
        
        client.post(f"/api/counters/?skill_id={skill1_id}", json={"name": "Counter 1A"})
        client.post(f"/api/counters/?skill_id={skill1_id}", json={"name": "Counter 1B"})
        client.post(f"/api/counters/?skill_id={skill2_id}", json={"name": "Counter 2"})
        
        response = client.get(f"/api/counters/?skill_id={skill1_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all(c["skill_id"] == skill1_id for c in data)


class TestGetCounter:
    """Tests for GET /counters/{counter_id} endpoint."""

    def test_get_counter_by_id(self):
        """Test getting a counter by ID."""
        skill_id = create_test_skill()
        create_response = client.post(
            f"/api/counters/?skill_id={skill_id}",
            json={"name": "Test Counter", "value": 42.0}
        )
        counter_id = create_response.json()["id"]
        
        response = client.get(f"/api/counters/{counter_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == counter_id
        assert data["name"] == "Test Counter"
        assert data["value"] == 42.0

    def test_get_nonexistent_counter(self):
        """Test getting a counter that doesn't exist."""
        response = client.get("/api/counters/999")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestUpdateCounter:
    """Tests for PATCH /counters/{counter_id} endpoint."""

    def test_update_counter_value(self):
        """Test updating counter value."""
        skill_id = create_test_skill()
        create_response = client.post(
            f"/api/counters/?skill_id={skill_id}",
            json={"name": "Test", "value": 10.0}
        )
        counter_id = create_response.json()["id"]
        
        response = client.patch(
            f"/api/counters/{counter_id}",
            json={"value": 25.0}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["value"] == 25.0
        assert data["name"] == "Test"  # Unchanged

    def test_update_counter_name(self):
        """Test updating counter name."""
        skill_id = create_test_skill()
        create_response = client.post(
            f"/api/counters/?skill_id={skill_id}",
            json={"name": "Old Name"}
        )
        counter_id = create_response.json()["id"]
        
        response = client.patch(
            f"/api/counters/{counter_id}",
            json={"name": "New Name"}
        )
        
        assert response.status_code == 200
        assert response.json()["name"] == "New Name"

    def test_update_counter_multiple_fields(self):
        """Test updating multiple counter fields."""
        skill_id = create_test_skill()
        create_response = client.post(
            f"/api/counters/?skill_id={skill_id}",
            json={"name": "Test", "value": 5.0, "unit": "old"}
        )
        counter_id = create_response.json()["id"]
        
        response = client.patch(
            f"/api/counters/{counter_id}",
            json={"name": "Updated", "value": 15.0, "unit": "new", "target": 100.0}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated"
        assert data["value"] == 15.0
        assert data["unit"] == "new"
        assert data["target"] == 100.0

    def test_update_counter_not_found(self):
        """Test updating non-existent counter."""
        response = client.patch(
            "/api/counters/999",
            json={"value": 10.0}
        )
        
        assert response.status_code == 404

    def test_update_counter_negative_value_rejected(self):
        """Test that negative values are rejected on update."""
        skill_id = create_test_skill()
        create_response = client.post(
            f"/api/counters/?skill_id={skill_id}",
            json={"name": "Test", "value": 10.0}
        )
        counter_id = create_response.json()["id"]
        
        response = client.patch(
            f"/api/counters/{counter_id}",
            json={"value": -5.0}
        )
        
        assert response.status_code == 422


class TestDeleteCounter:
    """Tests for DELETE /counters/{counter_id} endpoint."""

    def test_delete_counter(self):
        """Test deleting a counter."""
        skill_id = create_test_skill()
        create_response = client.post(
            f"/api/counters/?skill_id={skill_id}",
            json={"name": "Test Counter"}
        )
        counter_id = create_response.json()["id"]
        
        response = client.delete(f"/api/counters/{counter_id}")
        
        assert response.status_code == 204
        
        # Verify counter is deleted
        get_response = client.get(f"/api/counters/{counter_id}")
        assert get_response.status_code == 404

    def test_delete_counter_not_found(self):
        """Test deleting non-existent counter."""
        response = client.delete("/api/counters/999")
        
        assert response.status_code == 404

    def test_delete_one_of_multiple_counters(self):
        """Test deleting one counter doesn't affect others."""
        skill_id = create_test_skill()
        
        counter1_response = client.post(
            f"/api/counters/?skill_id={skill_id}",
            json={"name": "Counter 1"}
        )
        counter2_response = client.post(
            f"/api/counters/?skill_id={skill_id}",
            json={"name": "Counter 2"}
        )
        
        counter1_id = counter1_response.json()["id"]
        counter2_id = counter2_response.json()["id"]
        
        # Delete counter 1
        delete_response = client.delete(f"/api/counters/{counter1_id}")
        assert delete_response.status_code == 204
        
        # Counter 2 should still exist
        get_response = client.get(f"/api/counters/{counter2_id}")
        assert get_response.status_code == 200
        assert get_response.json()["name"] == "Counter 2"


class TestIncrementCounter:
    """Tests for POST /counters/{counter_id}/increment endpoint."""

    def test_increment_counter_default(self):
        """Test incrementing counter by default amount (1.0)."""
        skill_id = create_test_skill()
        create_response = client.post(
            f"/api/counters/?skill_id={skill_id}",
            json={"name": "Test", "value": 5.0}
        )
        counter_id = create_response.json()["id"]
        
        response = client.post(f"/api/counters/{counter_id}/increment")
        
        assert response.status_code == 200
        assert response.json()["value"] == 6.0

    def test_increment_counter_custom_amount(self):
        """Test incrementing counter by custom amount."""
        skill_id = create_test_skill()
        create_response = client.post(
            f"/api/counters/?skill_id={skill_id}",
            json={"name": "Test", "value": 10.0}
        )
        counter_id = create_response.json()["id"]
        
        response = client.post(f"/api/counters/{counter_id}/increment?amount=5.5")
        
        assert response.status_code == 200
        assert response.json()["value"] == 15.5

    def test_increment_counter_decimal(self):
        """Test incrementing by decimal amounts."""
        skill_id = create_test_skill()
        create_response = client.post(
            f"/api/counters/?skill_id={skill_id}",
            json={"name": "Test", "value": 1.25}
        )
        counter_id = create_response.json()["id"]
        
        response = client.post(f"/api/counters/{counter_id}/increment?amount=0.75")
        
        assert response.status_code == 200
        assert response.json()["value"] == 2.0

    def test_increment_counter_multiple_times(self):
        """Test incrementing counter multiple times."""
        skill_id = create_test_skill()
        create_response = client.post(
            f"/api/counters/?skill_id={skill_id}",
            json={"name": "Test", "value": 0.0}
        )
        counter_id = create_response.json()["id"]
        
        client.post(f"/api/counters/{counter_id}/increment?amount=3.0")
        client.post(f"/api/counters/{counter_id}/increment?amount=2.0")
        response = client.post(f"/api/counters/{counter_id}/increment?amount=1.0")
        
        assert response.status_code == 200
        assert response.json()["value"] == 6.0

    def test_increment_counter_not_found(self):
        """Test incrementing non-existent counter."""
        response = client.post("/api/counters/999/increment")
        
        assert response.status_code == 404

    def test_increment_counter_would_be_negative(self):
        """Test that incrementing with negative amount that would make value negative is rejected."""
        skill_id = create_test_skill()
        create_response = client.post(
            f"/api/counters/?skill_id={skill_id}",
            json={"name": "Test", "value": 5.0}
        )
        counter_id = create_response.json()["id"]
        
        response = client.post(f"/api/counters/{counter_id}/increment?amount=-10.0")
        
        assert response.status_code == 400
        assert "negative" in response.json()["detail"].lower()

    def test_decrement_counter_valid(self):
        """Test decrementing counter (negative increment) when result is non-negative."""
        skill_id = create_test_skill()
        create_response = client.post(
            f"/api/counters/?skill_id={skill_id}",
            json={"name": "Test", "value": 10.0}
        )
        counter_id = create_response.json()["id"]
        
        response = client.post(f"/api/counters/{counter_id}/increment?amount=-3.0")
        
        assert response.status_code == 200
        assert response.json()["value"] == 7.0


class TestCounterIntegration:
    """Integration tests for counter workflows."""

    def test_full_counter_lifecycle(self):
        """Test complete counter lifecycle: create, update, increment, delete."""
        # Create skill
        skill_id = create_test_skill("Python")
        
        # Create counter
        create_response = client.post(
            f"/api/counters/?skill_id={skill_id}",
            json={"name": "Practice Hours", "unit": "hours", "target": 100.0}
        )
        assert create_response.status_code == 201
        counter_id = create_response.json()["id"]
        
        # Increment
        client.post(f"/api/counters/{counter_id}/increment?amount=2.5")
        client.post(f"/api/counters/{counter_id}/increment?amount=1.5")
        
        # Update
        update_response = client.patch(
            f"/api/counters/{counter_id}",
            json={"name": "Total Practice Hours"}
        )
        assert update_response.status_code == 200
        assert update_response.json()["value"] == 4.0
        
        # Delete
        delete_response = client.delete(f"/api/counters/{counter_id}")
        assert delete_response.status_code == 204

    def test_multiple_counters_per_skill(self):
        """Test managing multiple counters for a single skill."""
        skill_id = create_test_skill("Data Science")
        
        # Create multiple counters
        hours_response = client.post(
            f"/api/counters/?skill_id={skill_id}",
            json={"name": "Study Hours", "unit": "hours"}
        )
        exercises_response = client.post(
            f"/api/counters/?skill_id={skill_id}",
            json={"name": "Exercises Done", "unit": "exercises"}
        )
        
        hours_id = hours_response.json()["id"]
        exercises_id = exercises_response.json()["id"]
        
        # Update them independently
        client.post(f"/api/counters/{hours_id}/increment?amount=5.0")
        client.post(f"/api/counters/{exercises_id}/increment?amount=10.0")
        
        # Verify both updated correctly
        hours_data = client.get(f"/api/counters/{hours_id}").json()
        exercises_data = client.get(f"/api/counters/{exercises_id}").json()
        
        assert hours_data["value"] == 5.0
        assert exercises_data["value"] == 10.0
