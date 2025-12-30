from fastapi.testclient import TestClient
from app.main import app
import pytest

client = TestClient(app)


def test_root_redirects_to_docs():
    """Test that root redirects to API documentation."""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/docs"


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_favicon():
    response = client.get("/favicon.ico")
    assert response.status_code == 204


def test_version():
    """Test version endpoint returns deployment info."""
    response = client.get("/version")
    assert response.status_code == 200

    data = response.json()
    assert "commit" in data
    assert "service" in data
    assert "version" in data


class TestClearAllData:
    """Tests for DELETE /api/data endpoint."""

    @pytest.fixture(autouse=True)
    def clear_before_test(self):
        """Clear all data before each test."""
        client.delete("/api/data")
        yield
        client.delete("/api/data")

    def test_clear_all_data_deletes_skills_and_counters(self):
        """Test that clear all data removes all skills and counters."""
        # Create some skills
        skill1 = client.post("/api/skills/", json={"name": "Python"}).json()
        skill2 = client.post("/api/skills/", json={"name": "JavaScript"}).json()
        
        # Add counters
        client.post(f"/api/counters/?skill_id={skill1['id']}", json={
            "name": "Hours",
            "value": 10
        })
        client.post(f"/api/counters/?skill_id={skill2['id']}", json={
            "name": "Projects",
            "value": 5
        })
        
        # Verify data exists
        skills = client.get("/api/skills/").json()
        assert len(skills) == 2
        
        counters = client.get("/api/counters/").json()
        assert len(counters) == 2
        
        # Clear all data
        response = client.delete("/api/data")
        assert response.status_code == 204
        
        # Verify everything is deleted
        skills = client.get("/api/skills/").json()
        assert len(skills) == 0
        
        counters = client.get("/api/counters/").json()
        assert len(counters) == 0

    def test_clear_all_data_with_nested_hierarchy(self):
        """Test clear all data works with complex nested hierarchies."""
        # Create complex hierarchy
        root = client.post("/api/skills/", json={"name": "Root"}).json()
        child1 = client.post(f"/api/skills/{root['id']}/children", json={"name": "Child1"}).json()
        child2 = client.post(f"/api/skills/{root['id']}/children", json={"name": "Child2"}).json()
        grandchild = client.post(f"/api/skills/{child1['id']}/children", json={"name": "Grandchild"}).json()
        
        # Add counters at multiple levels
        for skill_id in [root['id'], child1['id'], child2['id'], grandchild['id']]:
            client.post(f"/api/counters/?skill_id={skill_id}", json={
                "name": "Counter",
                "value": 1
            })
        
        # Verify data exists
        skills = client.get("/api/skills/").json()
        assert len(skills) == 4
        
        counters = client.get("/api/counters/").json()
        assert len(counters) == 4
        
        # Clear all
        response = client.delete("/api/data")
        assert response.status_code == 204
        
        # Verify all deleted
        assert len(client.get("/api/skills/").json()) == 0
        assert len(client.get("/api/counters/").json()) == 0

    def test_clear_all_data_when_already_empty(self):
        """Test clear all data works when database is already empty."""
        # Ensure empty
        client.delete("/api/data")
        
        # Clear again
        response = client.delete("/api/data")
        assert response.status_code == 204
        
        # Still empty
        assert len(client.get("/api/skills/").json()) == 0
        assert len(client.get("/api/counters/").json()) == 0

    def test_can_add_data_after_clearing(self):
        """Test that new data can be added after clearing all data."""
        # Add initial data
        skill1 = client.post("/api/skills/", json={"name": "Skill1"}).json()
        client.post(f"/api/counters/?skill_id={skill1['id']}", json={
            "name": "Counter1",
            "value": 10
        })
        
        # Clear
        client.delete("/api/data")
        
        # Add new data
        skill2 = client.post("/api/skills/", json={"name": "Skill2"}).json()
        assert skill2['name'] == "Skill2"
        
        counter2 = client.post(f"/api/counters/?skill_id={skill2['id']}", json={
            "name": "Counter2",
            "value": 20
        }).json()
        assert counter2['value'] == 20
        
        # Verify only new data exists
        skills = client.get("/api/skills/").json()
        assert len(skills) == 1
        assert skills[0]['name'] == "Skill2"
        
        counters = client.get("/api/counters/").json()
        assert len(counters) == 1
        assert counters[0]['name'] == "Counter2"

    def test_clear_resets_id_counters(self):
        """Test that clearing data resets ID counters to start from 1."""
        # Add skill
        skill1 = client.post("/api/skills/", json={"name": "Skill1"}).json()
        assert skill1['id'] == 1
        
        # Clear
        client.delete("/api/data")
        
        # Add new skill - should get ID 1 again
        skill2 = client.post("/api/skills/", json={"name": "Skill2"}).json()
        assert skill2['id'] == 1
