"""Tests for Skills API - Root skill creation."""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.routers.skills import skills_db, next_skill_id

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_skills_db():
    """Reset skills database before each test."""
    global next_skill_id
    skills_db.clear()
    # Reset the module-level variable
    import app.routers.skills as skills_module
    skills_module.next_skill_id = 1
    yield
    skills_db.clear()


class TestCreateRootSkill:
    """Tests for POST /skills endpoint - creating root skills."""

    def test_create_root_skill_success(self):
        """Test successfully creating a root skill."""
        response = client.post(
            "/skills/",
            json={"name": "Programming", "parent_id": None}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["id"] == 1
        assert data["name"] == "Programming"
        assert data["parent_id"] is None

    def test_create_root_skill_minimal(self):
        """Test creating root skill with minimal data (no parent_id field)."""
        response = client.post(
            "/skills/",
            json={"name": "Python"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["id"] == 1
        assert data["name"] == "Python"
        assert data["parent_id"] is None

    def test_create_multiple_root_skills(self):
        """Test creating multiple root skills with different names."""
        # Create first root skill
        response1 = client.post("/skills/", json={"name": "Programming"})
        assert response1.status_code == 201
        assert response1.json()["id"] == 1
        
        # Create second root skill
        response2 = client.post("/skills/", json={"name": "Mathematics"})
        assert response2.status_code == 201
        assert response2.json()["id"] == 2
        
        # Create third root skill
        response3 = client.post("/skills/", json={"name": "Languages"})
        assert response3.status_code == 201
        assert response3.json()["id"] == 3

    def test_create_root_skill_name_required(self):
        """Test that name is required."""
        response = client.post(
            "/skills/",
            json={"parent_id": None}
        )
        
        assert response.status_code == 422
        assert "name" in response.text.lower()

    def test_create_root_skill_name_not_empty(self):
        """Test that name cannot be empty."""
        response = client.post(
            "/skills/",
            json={"name": "", "parent_id": None}
        )
        
        assert response.status_code == 422

    def test_create_root_skill_name_max_length(self):
        """Test name maximum length validation."""
        long_name = "x" * 256
        response = client.post(
            "/skills/",
            json={"name": long_name, "parent_id": None}
        )
        
        assert response.status_code == 422


class TestUniqueRootNameValidation:
    """Tests for unique root skill name validation."""

    def test_duplicate_root_name_rejected(self):
        """Test that duplicate root skill names are rejected."""
        # Create first root skill
        response1 = client.post("/skills/", json={"name": "Programming"})
        assert response1.status_code == 201
        
        # Try to create another root skill with same name
        response2 = client.post("/skills/", json={"name": "Programming"})
        assert response2.status_code == 409
        assert "already exists" in response2.json()["detail"]

    def test_duplicate_root_name_case_insensitive(self):
        """Test that root name uniqueness is case-insensitive."""
        # Create root skill with lowercase
        response1 = client.post("/skills/", json={"name": "programming"})
        assert response1.status_code == 201
        
        # Try with uppercase
        response2 = client.post("/skills/", json={"name": "PROGRAMMING"})
        assert response2.status_code == 409
        
        # Try with mixed case
        response3 = client.post("/skills/", json={"name": "Programming"})
        assert response3.status_code == 409

    def test_root_names_can_differ(self):
        """Test that different root names are allowed."""
        response1 = client.post("/skills/", json={"name": "Programming"})
        assert response1.status_code == 201
        
        response2 = client.post("/skills/", json={"name": "Programming Skills"})
        assert response2.status_code == 201
        
        response3 = client.post("/skills/", json={"name": "Python Programming"})
        assert response3.status_code == 201


class TestSubskillRejection:
    """Tests for rejecting subskill creation at root endpoint."""

    def test_reject_skill_with_parent_id(self):
        """Test that skills with parent_id are rejected at root endpoint."""
        # First create a root skill
        response1 = client.post("/skills/", json={"name": "Programming"})
        assert response1.status_code == 201
        parent_id = response1.json()["id"]
        
        # Try to create child at root endpoint
        response2 = client.post(
            "/skills/",
            json={"name": "Python", "parent_id": parent_id}
        )
        
        assert response2.status_code == 400
        assert "subskill" in response2.json()["detail"].lower()
        assert "children" in response2.json()["detail"].lower()


class TestListSkills:
    """Tests for GET /skills endpoint."""

    def test_list_empty_skills(self):
        """Test listing skills when none exist."""
        response = client.get("/skills/")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_single_skill(self):
        """Test listing skills with one skill."""
        client.post("/skills/", json={"name": "Programming"})
        
        response = client.get("/skills/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Programming"

    def test_list_multiple_skills(self):
        """Test listing multiple skills."""
        client.post("/skills/", json={"name": "Programming"})
        client.post("/skills/", json={"name": "Mathematics"})
        client.post("/skills/", json={"name": "Languages"})
        
        response = client.get("/skills/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        names = [skill["name"] for skill in data]
        assert "Programming" in names
        assert "Mathematics" in names
        assert "Languages" in names


class TestGetSkill:
    """Tests for GET /skills/{id} endpoint."""

    def test_get_skill_by_id(self):
        """Test retrieving a skill by ID."""
        create_response = client.post("/skills/", json={"name": "Programming"})
        skill_id = create_response.json()["id"]
        
        response = client.get(f"/skills/{skill_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == skill_id
        assert data["name"] == "Programming"
        assert data["parent_id"] is None

    def test_get_nonexistent_skill(self):
        """Test retrieving a skill that doesn't exist."""
        response = client.get("/skills/999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_multiple_skills_by_id(self):
        """Test retrieving multiple skills by their IDs."""
        response1 = client.post("/skills/", json={"name": "Programming"})
        response2 = client.post("/skills/", json={"name": "Mathematics"})
        
        id1 = response1.json()["id"]
        id2 = response2.json()["id"]
        
        get_response1 = client.get(f"/skills/{id1}")
        assert get_response1.json()["name"] == "Programming"
        
        get_response2 = client.get(f"/skills/{id2}")
        assert get_response2.json()["name"] == "Mathematics"


class TestRootSkillIntegration:
    """Integration tests for root skill operations."""

    def test_create_and_retrieve_flow(self):
        """Test complete flow of creating and retrieving a root skill."""
        # Create
        create_response = client.post("/skills/", json={"name": "Programming"})
        assert create_response.status_code == 201
        skill_id = create_response.json()["id"]
        
        # List
        list_response = client.get("/skills/")
        assert len(list_response.json()) == 1
        
        # Get by ID
        get_response = client.get(f"/skills/{skill_id}")
        assert get_response.json()["name"] == "Programming"

    def test_multiple_roots_independent(self):
        """Test that multiple root skills are independent."""
        # Create multiple root skills
        prog_response = client.post("/skills/", json={"name": "Programming"})
        math_response = client.post("/skills/", json={"name": "Mathematics"})
        lang_response = client.post("/skills/", json={"name": "Languages"})
        
        # All should be root skills (parent_id=None)
        assert prog_response.json()["parent_id"] is None
        assert math_response.json()["parent_id"] is None
        assert lang_response.json()["parent_id"] is None
        
        # All should have different IDs
        ids = [
            prog_response.json()["id"],
            math_response.json()["id"],
            lang_response.json()["id"]
        ]
        assert len(set(ids)) == 3
