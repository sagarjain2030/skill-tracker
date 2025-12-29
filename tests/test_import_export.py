"""Tests for skill tree import/export endpoints."""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.routers import skills, counters
from app.storage import clear_all_data

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_database():
    """Reset database before each test."""
    clear_all_data()
    skills.skills_db.clear()
    counters.counters_db.clear()
    skills.next_skill_id = 1
    counters.next_counter_id = 1
    yield
    clear_all_data()
    skills.skills_db.clear()
    counters.counters_db.clear()
    skills.next_skill_id = 1
    counters.next_counter_id = 1


class TestImportSkillTree:
    """Tests for POST /api/skills/import endpoint."""

    def test_import_single_root(self):
        """Test importing a single root skill without children."""
        import_data = [
            {
                "name": "Python",
                "children": []
            }
        ]
        
        response = client.post("/api/skills/import", json=import_data)
        
        assert response.status_code == 201
        result = response.json()
        assert len(result) == 1
        assert result[0]["name"] == "Python"
        assert result[0]["id"] == 1
        assert result[0]["children"] == []
        
        # Verify in database
        skills = client.get("/api/skills/").json()
        assert len(skills) == 1
        assert skills[0]["name"] == "Python"

    def test_import_tree_with_children(self):
        """Test importing a tree with nested children."""
        import_data = [
            {
                "name": "Programming",
                "children": [
                    {"name": "Python", "children": []},
                    {"name": "JavaScript", "children": []}
                ]
            }
        ]
        
        response = client.post("/api/skills/import", json=import_data)
        
        assert response.status_code == 201
        result = response.json()
        assert len(result) == 1
        
        root = result[0]
        assert root["name"] == "Programming"
        assert root["id"] == 1
        assert len(root["children"]) == 2
        
        # Check children have sequential IDs
        assert root["children"][0]["name"] == "Python"
        assert root["children"][0]["id"] == 2
        assert root["children"][1]["name"] == "JavaScript"
        assert root["children"][1]["id"] == 3
        
        # Verify all skills created
        skills = client.get("/api/skills/").json()
        assert len(skills) == 3

    def test_import_deep_hierarchy(self):
        """Test importing a deeply nested hierarchy."""
        import_data = [
            {
                "name": "Tech",
                "children": [
                    {
                        "name": "Backend",
                        "children": [
                            {
                                "name": "Python",
                                "children": [
                                    {"name": "FastAPI", "children": []}
                                ]
                            }
                        ]
                    }
                ]
            }
        ]
        
        response = client.post("/api/skills/import", json=import_data)
        
        assert response.status_code == 201
        result = response.json()
        
        # Navigate down the hierarchy
        tech = result[0]
        assert tech["name"] == "Tech"
        
        backend = tech["children"][0]
        assert backend["name"] == "Backend"
        
        python = backend["children"][0]
        assert python["name"] == "Python"
        
        fastapi = python["children"][0]
        assert fastapi["name"] == "FastAPI"
        assert fastapi["children"] == []
        
        # Verify all 4 skills created
        skills = client.get("/api/skills/").json()
        assert len(skills) == 4

    def test_import_multiple_roots(self):
        """Test importing multiple root skills."""
        import_data = [
            {
                "name": "Programming",
                "children": [
                    {"name": "Python", "children": []}
                ]
            },
            {
                "name": "Design",
                "children": [
                    {"name": "UI/UX", "children": []}
                ]
            }
        ]
        
        response = client.post("/api/skills/import", json=import_data)
        
        assert response.status_code == 201
        result = response.json()
        assert len(result) == 2
        
        # Check both trees
        assert result[0]["name"] == "Programming"
        assert len(result[0]["children"]) == 1
        
        assert result[1]["name"] == "Design"
        assert len(result[1]["children"]) == 1
        
        # Verify all 4 skills created
        skills = client.get("/api/skills/").json()
        assert len(skills) == 4

    def test_import_complex_tree_structure(self):
        """Test importing complex tree with multiple branches."""
        import_data = [
            {
                "name": "Skills",
                "children": [
                    {
                        "name": "Technical",
                        "children": [
                            {"name": "Python", "children": []},
                            {"name": "JavaScript", "children": []}
                        ]
                    },
                    {
                        "name": "Soft Skills",
                        "children": [
                            {"name": "Communication", "children": []},
                            {"name": "Leadership", "children": []}
                        ]
                    }
                ]
            }
        ]
        
        response = client.post("/api/skills/import", json=import_data)
        
        assert response.status_code == 201
        result = response.json()
        
        root = result[0]
        assert root["name"] == "Skills"
        assert len(root["children"]) == 2
        
        technical = root["children"][0]
        assert technical["name"] == "Technical"
        assert len(technical["children"]) == 2
        
        soft_skills = root["children"][1]
        assert soft_skills["name"] == "Soft Skills"
        assert len(soft_skills["children"]) == 2
        
        # Verify all 7 skills created
        skills = client.get("/api/skills/").json()
        assert len(skills) == 7

    def test_import_empty_list(self):
        """Test importing empty list creates no skills."""
        response = client.post("/api/skills/import", json=[])
        
        assert response.status_code == 201
        result = response.json()
        assert result == []
        
        skills = client.get("/api/skills/").json()
        assert len(skills) == 0

    def test_import_duplicate_root_name(self):
        """Test importing skill with duplicate root name fails."""
        # Create existing root skill
        client.post("/api/skills/", json={"name": "Python"})
        
        # Try to import tree with same root name
        import_data = [{"name": "Python", "children": []}]
        
        response = client.post("/api/skills/import", json=import_data)
        
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]

    def test_import_appends_to_existing_skills(self):
        """Test importing appends to existing skills."""
        # Create existing skill
        client.post("/api/skills/", json={"name": "Existing"})
        
        # Import new tree
        import_data = [{"name": "New", "children": []}]
        response = client.post("/api/skills/import", json=import_data)
        
        assert response.status_code == 201
        
        # Both should exist
        skills = client.get("/api/skills/").json()
        assert len(skills) == 2
        names = {skill["name"] for skill in skills}
        assert names == {"Existing", "New"}

    def test_import_preserves_tree_structure(self):
        """Test import preserves exact tree structure."""
        import_data = [
            {
                "name": "Root",
                "children": [
                    {
                        "name": "A",
                        "children": [
                            {"name": "A1", "children": []},
                            {"name": "A2", "children": []}
                        ]
                    },
                    {
                        "name": "B",
                        "children": [
                            {"name": "B1", "children": []}
                        ]
                    }
                ]
            }
        ]
        
        response = client.post("/api/skills/import", json=import_data)
        assert response.status_code == 201
        
        # Get tree and verify structure
        tree = client.get("/api/skills/tree").json()
        assert len(tree) == 1
        
        root = tree[0]
        assert root["name"] == "Root"
        assert len(root["children"]) == 2
        
        # Check A branch
        a = next(c for c in root["children"] if c["name"] == "A")
        assert len(a["children"]) == 2
        assert {c["name"] for c in a["children"]} == {"A1", "A2"}
        
        # Check B branch
        b = next(c for c in root["children"] if c["name"] == "B")
        assert len(b["children"]) == 1
        assert b["children"][0]["name"] == "B1"


class TestExportSkillTree:
    """Tests for GET /api/skills/export endpoint."""

    def test_export_empty_tree(self):
        """Test exporting when no skills exist."""
        response = client.get("/api/skills/export")
        
        assert response.status_code == 200
        assert response.json() == []

    def test_export_single_root(self):
        """Test exporting a single root skill."""
        created = client.post("/api/skills/", json={"name": "Python"}).json()
        
        response = client.get("/api/skills/export")
        
        assert response.status_code == 200
        result = response.json()
        assert len(result) == 1
        assert result[0]["id"] == created["id"]
        assert result[0]["name"] == "Python"
        assert result[0]["children"] == []

    def test_export_tree_with_children(self):
        """Test exporting tree with nested children."""
        root = client.post("/api/skills/", json={"name": "Tech"}).json()
        child1 = client.post(f"/api/skills/{root['id']}/children", json={"name": "Python"}).json()
        child2 = client.post(f"/api/skills/{root['id']}/children", json={"name": "JavaScript"}).json()
        
        response = client.get("/api/skills/export")
        
        assert response.status_code == 200
        result = response.json()
        assert len(result) == 1
        
        exported_root = result[0]
        assert exported_root["id"] == root["id"]
        assert exported_root["name"] == "Tech"
        assert len(exported_root["children"]) == 2
        
        child_ids = {c["id"] for c in exported_root["children"]}
        assert child_ids == {child1["id"], child2["id"]}

    def test_export_deep_hierarchy(self):
        """Test exporting deeply nested hierarchy."""
        a = client.post("/api/skills/", json={"name": "A"}).json()
        b = client.post(f"/api/skills/{a['id']}/children", json={"name": "B"}).json()
        c = client.post(f"/api/skills/{b['id']}/children", json={"name": "C"}).json()
        client.post(f"/api/skills/{c['id']}/children", json={"name": "D"})
        
        response = client.get("/api/skills/export")
        
        assert response.status_code == 200
        result = response.json()
        
        # Navigate down the hierarchy
        assert result[0]["name"] == "A"
        assert result[0]["children"][0]["name"] == "B"
        assert result[0]["children"][0]["children"][0]["name"] == "C"
        assert result[0]["children"][0]["children"][0]["children"][0]["name"] == "D"

    def test_export_multiple_roots(self):
        """Test exporting multiple root skills."""
        root1 = client.post("/api/skills/", json={"name": "Tech"}).json()
        root2 = client.post("/api/skills/", json={"name": "Business"}).json()
        
        client.post(f"/api/skills/{root1['id']}/children", json={"name": "Python"})
        client.post(f"/api/skills/{root2['id']}/children", json={"name": "Marketing"})
        
        response = client.get("/api/skills/export")
        
        assert response.status_code == 200
        result = response.json()
        assert len(result) == 2
        
        names = {r["name"] for r in result}
        assert names == {"Tech", "Business"}

    def test_export_complex_structure(self):
        """Test exporting complex tree with multiple branches."""
        root = client.post("/api/skills/", json={"name": "Root"}).json()
        
        a = client.post(f"/api/skills/{root['id']}/children", json={"name": "A"}).json()
        b = client.post(f"/api/skills/{root['id']}/children", json={"name": "B"}).json()
        
        client.post(f"/api/skills/{a['id']}/children", json={"name": "A1"})
        client.post(f"/api/skills/{a['id']}/children", json={"name": "A2"})
        client.post(f"/api/skills/{b['id']}/children", json={"name": "B1"})
        
        response = client.get("/api/skills/export")
        
        assert response.status_code == 200
        result = response.json()
        
        exported_root = result[0]
        assert exported_root["name"] == "Root"
        assert len(exported_root["children"]) == 2
        
        # Check A branch
        a_node = next(c for c in exported_root["children"] if c["name"] == "A")
        assert len(a_node["children"]) == 2
        
        # Check B branch
        b_node = next(c for c in exported_root["children"] if c["name"] == "B")
        assert len(b_node["children"]) == 1


class TestUpdateSkillTree:
    """Tests for PUT /api/skills/import endpoint."""

    def test_update_replaces_all_skills(self):
        """Test that PUT /import replaces all existing skills."""
        # Create initial skills
        client.post("/api/skills/", json={"name": "Old"})
        
        # Update with new tree
        import_data = [{"name": "New", "children": []}]
        response = client.put("/api/skills/import", json=import_data)
        
        assert response.status_code == 200
        
        # Verify old skill is gone
        skills = client.get("/api/skills/").json()
        assert len(skills) == 1
        assert skills[0]["name"] == "New"

    def test_update_with_empty_clears_all(self):
        """Test updating with empty list clears all skills."""
        # Create initial skills
        client.post("/api/skills/", json={"name": "Skill1"})
        client.post("/api/skills/", json={"name": "Skill2"})
        
        # Update with empty list
        response = client.put("/api/skills/import", json=[])
        
        assert response.status_code == 200
        result = response.json()
        assert result == []
        
        # Verify all skills cleared
        skills = client.get("/api/skills/").json()
        assert len(skills) == 0

    def test_update_with_complex_tree(self):
        """Test updating with complex tree structure."""
        # Create initial skill
        client.post("/api/skills/", json={"name": "Old"})
        
        # Update with new complex tree
        import_data = [
            {
                "name": "Programming",
                "children": [
                    {"name": "Python", "children": []},
                    {"name": "JavaScript", "children": []}
                ]
            }
        ]
        response = client.put("/api/skills/import", json=import_data)
        
        assert response.status_code == 200
        result = response.json()
        
        assert len(result) == 1
        assert result[0]["name"] == "Programming"
        assert len(result[0]["children"]) == 2
        
        # Verify only new skills exist
        skills = client.get("/api/skills/").json()
        assert len(skills) == 3
        names = {s["name"] for s in skills}
        assert names == {"Programming", "Python", "JavaScript"}

    def test_update_resets_ids(self):
        """Test that update resets skill IDs to start from 1."""
        # Create skills (IDs will be 1, 2, 3)
        client.post("/api/skills/", json={"name": "A"})
        client.post("/api/skills/", json={"name": "B"})
        client.post("/api/skills/", json={"name": "C"})
        
        # Update with new tree
        import_data = [{"name": "New", "children": []}]
        response = client.put("/api/skills/import", json=import_data)
        
        assert response.status_code == 200
        result = response.json()
        
        # New skill should have ID 1
        assert result[0]["id"] == 1

    def test_update_multiple_times(self):
        """Test updating multiple times."""
        # First update
        import_data1 = [{"name": "Tree1", "children": []}]
        client.put("/api/skills/import", json=import_data1)
        
        # Second update
        import_data2 = [{"name": "Tree2", "children": []}]
        response = client.put("/api/skills/import", json=import_data2)
        
        assert response.status_code == 200
        
        # Only Tree2 should exist
        skills = client.get("/api/skills/").json()
        assert len(skills) == 1
        assert skills[0]["name"] == "Tree2"


class TestImportExportRoundTrip:
    """Tests for import/export round-trip consistency."""

    def test_export_import_roundtrip(self):
        """Test that exporting and re-importing preserves structure."""
        # Create initial tree
        root = client.post("/api/skills/", json={"name": "Root"}).json()
        child1 = client.post(f"/api/skills/{root['id']}/children", json={"name": "Child1"}).json()
        client.post(f"/api/skills/{root['id']}/children", json={"name": "Child2"})
        client.post(f"/api/skills/{child1['id']}/children", json={"name": "Grandchild"})
        
        # Export
        export_response = client.get("/api/skills/export")
        exported_data = export_response.json()
        
        # Clear and re-import (convert export format to import format)
        import_data = self._convert_export_to_import(exported_data)
        client.put("/api/skills/import", json=import_data)
        
        # Export again and compare structure
        new_export = client.get("/api/skills/export").json()
        
        # Structure should be identical (ignoring IDs)
        assert self._compare_structures(exported_data, new_export)

    def test_large_tree_export_import(self):
        """Test export/import with larger tree."""
        # Create tree with 10 skills
        root = client.post("/api/skills/", json={"name": "Root"}).json()
        
        for i in range(3):
            child = client.post(
                f"/api/skills/{root['id']}/children",
                json={"name": f"Child{i}"}
            ).json()
            
            for j in range(2):
                client.post(
                    f"/api/skills/{child['id']}/children",
                    json={"name": f"Grandchild{i}-{j}"}
                )
        
        # Export
        exported = client.get("/api/skills/export").json()
        
        # Verify structure
        assert len(exported) == 1
        assert exported[0]["name"] == "Root"
        assert len(exported[0]["children"]) == 3
        
        for child in exported[0]["children"]:
            assert len(child["children"]) == 2

    @staticmethod
    def _convert_export_to_import(exported):
        """Convert export format to import format (remove IDs)."""
        def convert_node(node):
            return {
                "name": node["name"],
                "children": [convert_node(child) for child in node["children"]]
            }
        return [convert_node(tree) for tree in exported]

    @staticmethod
    def _compare_structures(tree1, tree2):
        """Compare tree structures ignoring IDs."""
        if len(tree1) != len(tree2):
            return False
        
        def compare_nodes(node1, node2):
            if node1["name"] != node2["name"]:
                return False
            if len(node1["children"]) != len(node2["children"]):
                return False
            for c1, c2 in zip(node1["children"], node2["children"]):
                if not compare_nodes(c1, c2):
                    return False
            return True
        
        for t1, t2 in zip(tree1, tree2):
            if not compare_nodes(t1, t2):
                return False
        return True


class TestImportExportWithCounters:
    """Tests for counter preservation in import/export."""

    def test_import_skill_with_counters(self):
        """Test importing a skill with counters."""
        import_data = [
            {
                "name": "Python Course",
                "counters": [
                    {"name": "Videos", "value": 0, "target": 50, "unit": None},
                    {"name": "Duration", "value": 0, "target": 120, "unit": "Mins"}
                ],
                "children": []
            }
        ]
        
        response = client.post("/api/skills/import", json=import_data)
        
        assert response.status_code == 201
        result = response.json()
        assert len(result) == 1
        
        # Check counters are in response
        assert len(result[0]["counters"]) == 2
        assert result[0]["counters"][0]["name"] == "Videos"
        assert result[0]["counters"][0]["value"] == 0
        assert result[0]["counters"][0]["target"] == 50
        assert result[0]["counters"][0]["unit"] is None
        
        assert result[0]["counters"][1]["name"] == "Duration"
        assert result[0]["counters"][1]["value"] == 0
        assert result[0]["counters"][1]["target"] == 120
        assert result[0]["counters"][1]["unit"] == "Mins"
        
        # Verify counters created in database
        skill_id = result[0]["id"]
        counters_response = client.get(f"/api/counters/?skill_id={skill_id}")
        counters = counters_response.json()
        assert len(counters) == 2

    def test_export_skill_with_counters(self):
        """Test exporting a skill with counters."""
        # Create skill
        skill = client.post("/api/skills/", json={"name": "JavaScript"}).json()
        skill_id = skill["id"]
        
        # Add counters
        client.post(f"/api/counters/?skill_id={skill_id}", json={
            "name": "Videos",
            "value": 10,
            "target": 25,
            "unit": None
        })
        client.post(f"/api/counters/?skill_id={skill_id}", json={
            "name": "Hours",
            "value": 5.5,
            "target": 15.0,
            "unit": "hrs"
        })
        
        # Export
        response = client.get("/api/skills/export")
        
        assert response.status_code == 200
        result = response.json()
        assert len(result) == 1
        
        # Check counters in export
        assert len(result[0]["counters"]) == 2
        assert result[0]["counters"][0]["name"] == "Videos"
        assert result[0]["counters"][0]["value"] == 10
        assert result[0]["counters"][0]["target"] == 25
        assert result[0]["counters"][0]["unit"] is None
        
        assert result[0]["counters"][1]["name"] == "Hours"
        assert result[0]["counters"][1]["value"] == 5.5
        assert result[0]["counters"][1]["target"] == 15.0
        assert result[0]["counters"][1]["unit"] == "hrs"

    def test_roundtrip_with_counters(self):
        """Test that counters survive export->import roundtrip."""
        # Create skill with counters
        skill = client.post("/api/skills/", json={"name": "AWS Course"}).json()
        skill_id = skill["id"]
        
        client.post(f"/api/counters/?skill_id={skill_id}", json={
            "name": "Videos",
            "value": 15,
            "target": 269,
            "unit": None
        })
        client.post(f"/api/counters/?skill_id={skill_id}", json={
            "name": "Duration",
            "value": 50,
            "target": 785,
            "unit": "Mins"
        })
        
        # Export
        exported = client.get("/api/skills/export").json()
        
        # Clear database
        client.put("/api/skills/import", json=[])
        
        # Re-import
        response = client.post("/api/skills/import", json=exported)
        
        assert response.status_code == 201
        result = response.json()
        
        # Verify counters preserved
        assert len(result[0]["counters"]) == 2
        assert result[0]["counters"][0]["name"] == "Videos"
        assert result[0]["counters"][0]["value"] == 15
        assert result[0]["counters"][0]["target"] == 269
        
        assert result[0]["counters"][1]["name"] == "Duration"
        assert result[0]["counters"][1]["value"] == 50
        assert result[0]["counters"][1]["target"] == 785
        assert result[0]["counters"][1]["unit"] == "Mins"

    def test_import_nested_tree_with_counters(self):
        """Test importing nested tree where multiple nodes have counters."""
        import_data = [
            {
                "name": "AWS Certification",
                "counters": [
                    {"name": "Progress", "value": 30, "target": 100, "unit": "%"}
                ],
                "children": [
                    {
                        "name": "EC2 Module",
                        "counters": [
                            {"name": "Videos", "value": 5, "target": 20, "unit": None},
                            {"name": "Labs", "value": 2, "target": 5, "unit": None}
                        ],
                        "children": []
                    },
                    {
                        "name": "S3 Module",
                        "counters": [
                            {"name": "Videos", "value": 8, "target": 15, "unit": None}
                        ],
                        "children": []
                    }
                ]
            }
        ]
        
        response = client.post("/api/skills/import", json=import_data)
        
        assert response.status_code == 201
        result = response.json()
        
        # Check root counters
        assert len(result[0]["counters"]) == 1
        assert result[0]["counters"][0]["name"] == "Progress"
        
        # Check first child counters
        assert len(result[0]["children"][0]["counters"]) == 2
        assert result[0]["children"][0]["counters"][0]["name"] == "Videos"
        assert result[0]["children"][0]["counters"][1]["name"] == "Labs"
        
        # Check second child counters
        assert len(result[0]["children"][1]["counters"]) == 1
        assert result[0]["children"][1]["counters"][0]["name"] == "Videos"

    def test_replace_all_with_counters(self):
        """Test that replace all (PUT /import) properly handles counters."""
        # Create initial tree with counters
        skill1 = client.post("/api/skills/", json={"name": "Old Skill"}).json()
        client.post(f"/api/counters/?skill_id={skill1['id']}", json={
            "name": "OldCounter",
            "value": 100,
            "target": 200,
            "unit": None
        })
        
        # Replace with new tree
        new_data = [
            {
                "name": "New Skill",
                "counters": [
                    {"name": "NewCounter", "value": 5, "target": 10, "unit": None}
                ],
                "children": []
            }
        ]
        
        response = client.put("/api/skills/import", json=new_data)
        
        assert response.status_code == 200
        result = response.json()
        
        # Verify old skill and counter are gone
        all_skills = client.get("/api/skills/").json()
        assert len(all_skills) == 1
        assert all_skills[0]["name"] == "New Skill"
        
        # Verify new counter exists
        assert len(result[0]["counters"]) == 1
        assert result[0]["counters"][0]["name"] == "NewCounter"
        assert result[0]["counters"][0]["value"] == 5
        
        # Verify old counter doesn't exist
        new_skill_id = result[0]["id"]
        counters = client.get(f"/api/counters/?skill_id={new_skill_id}").json()
        assert len(counters) == 1
        assert counters[0]["name"] == "NewCounter"

    def test_import_counter_without_target(self):
        """Test importing a counter without target (optional field)."""
        import_data = [
            {
                "name": "Skill",
                "counters": [
                    {"name": "Counter", "value": 10, "target": None, "unit": None}
                ],
                "children": []
            }
        ]
        
        response = client.post("/api/skills/import", json=import_data)
        
        assert response.status_code == 201
        result = response.json()
        assert result[0]["counters"][0]["target"] is None

    def test_import_counter_without_unit(self):
        """Test importing a counter without unit (optional field)."""
        import_data = [
            {
                "name": "Skill",
                "counters": [
                    {"name": "Count", "value": 5, "target": 10, "unit": None}
                ],
                "children": []
            }
        ]
        
        response = client.post("/api/skills/import", json=import_data)
        
        assert response.status_code == 201
        result = response.json()
        assert result[0]["counters"][0]["unit"] is None
