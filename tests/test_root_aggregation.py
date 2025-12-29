"""Tests for root skill aggregation endpoint."""
import pytest
from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_storage():
    """Reset storage before each test."""
    from app.routers.skills import skills_db
    from app.routers.counters import counters_db
    skills_db.clear()
    counters_db.clear()
    yield
    skills_db.clear()
    counters_db.clear()


class TestGetRootsSummary:
    """Tests for GET /api/skills/roots/summary endpoint."""
    
    def test_roots_summary_no_skills(self):
        """Test roots summary when no skills exist."""
        response = client.get("/api/skills/roots/summary")
        assert response.status_code == 200
        
        summaries = response.json()
        assert summaries == []
    
    def test_roots_summary_single_root_no_children(self):
        """Test roots summary with single root skill and no children."""
        # Create a root skill
        root = client.post("/api/skills/", json={"name": "Python"}).json()
        
        # Get roots summary
        response = client.get("/api/skills/roots/summary")
        assert response.status_code == 200
        
        summaries = response.json()
        assert len(summaries) == 1
        
        summary = summaries[0]
        assert summary["id"] == root["id"]
        assert summary["name"] == "Python"
        assert summary["parent_id"] is None
        assert summary["counter_totals"] == []
        assert summary["total_descendants"] == 0
        assert summary["direct_children_count"] == 0
        assert summary["children"] == []
    
    def test_roots_summary_single_root_with_children_and_counters(self):
        """Test roots summary with single root that has children and counters."""
        # Create hierarchy: Programming > Python > Django
        root = client.post("/api/skills/", json={"name": "Programming"}).json()
        child = client.post(f"/api/skills/{root['id']}/children", json={"name": "Python"}).json()
        grandchild = client.post(f"/api/skills/{child['id']}/children", json={"name": "Django"}).json()
        
        # Add counters at different levels
        client.post(f"/api/counters/?skill_id={root['id']}", json={
            "name": "Hours",
            "unit": "h",
            "value": 5.0
        })
        client.post(f"/api/counters/?skill_id={child['id']}", json={
            "name": "Hours",
            "unit": "h",
            "value": 10.0
        })
        client.post(f"/api/counters/?skill_id={grandchild['id']}", json={
            "name": "Hours",
            "unit": "h",
            "value": 3.5
        })
        
        # Get roots summary
        response = client.get("/api/skills/roots/summary")
        assert response.status_code == 200
        
        summaries = response.json()
        assert len(summaries) == 1
        
        summary = summaries[0]
        assert summary["id"] == root["id"]
        assert summary["name"] == "Programming"
        assert summary["total_descendants"] == 2  # Python, Django
        assert summary["direct_children_count"] == 1  # Python
        
        # Check aggregated counters
        assert len(summary["counter_totals"]) == 1
        hours = summary["counter_totals"][0]
        assert hours["name"] == "Hours"
        assert hours["unit"] == "h"
        assert hours["total"] == 18.5  # 5 + 10 + 3.5
        assert hours["count"] == 3
        
        # Check children structure
        assert len(summary["children"]) == 1
        python_summary = summary["children"][0]
        assert python_summary["name"] == "Python"
        assert len(python_summary["children"]) == 1
    
    def test_roots_summary_multiple_roots(self):
        """Test roots summary with multiple root skills."""
        # Create multiple root skills
        root1 = client.post("/api/skills/", json={"name": "Programming"}).json()
        root2 = client.post("/api/skills/", json={"name": "Design"}).json()
        root3 = client.post("/api/skills/", json={"name": "DevOps"}).json()
        print(root1, root2, root3)
        # Add children to first root
        client.post(f"/api/skills/{root1['id']}/children", json={"name": "Python"})
        client.post(f"/api/skills/{root1['id']}/children", json={"name": "JavaScript"})
        
        # Add child to second root
        client.post(f"/api/skills/{root2['id']}/children", json={"name": "Figma"})
        
        # Get roots summary
        response = client.get("/api/skills/roots/summary")
        assert response.status_code == 200
        
        summaries = response.json()
        assert len(summaries) == 3
        
        # Verify each root is included
        root_names = {s["name"] for s in summaries}
        assert root_names == {"Programming", "Design", "DevOps"}
        
        # Check descendants for each
        prog_summary = next(s for s in summaries if s["name"] == "Programming")
        assert prog_summary["total_descendants"] == 2
        assert prog_summary["direct_children_count"] == 2
        
        design_summary = next(s for s in summaries if s["name"] == "Design")
        assert design_summary["total_descendants"] == 1
        assert design_summary["direct_children_count"] == 1
        
        devops_summary = next(s for s in summaries if s["name"] == "DevOps")
        assert devops_summary["total_descendants"] == 0
        assert devops_summary["direct_children_count"] == 0
    
    def test_roots_summary_with_multiple_counter_types(self):
        """Test roots summary with multiple root skills having different counter types."""
        # Create two roots
        root1 = client.post("/api/skills/", json={"name": "Programming"}).json()
        root2 = client.post("/api/skills/", json={"name": "Fitness"}).json()
        
        # Add counters to first root
        client.post(f"/api/counters/?skill_id={root1['id']}", json={
            "name": "Hours",
            "unit": "h",
            "value": 100
        })
        client.post(f"/api/counters/?skill_id={root1['id']}", json={
            "name": "Projects",
            "unit": "count",
            "value": 5
        })
        
        # Add counters to second root
        client.post(f"/api/counters/?skill_id={root2['id']}", json={
            "name": "Workouts",
            "unit": "sessions",
            "value": 50
        })
        client.post(f"/api/counters/?skill_id={root2['id']}", json={
            "name": "Hours",
            "unit": "h",
            "value": 25
        })
        
        # Get roots summary
        response = client.get("/api/skills/roots/summary")
        summaries = response.json()
        
        # Check Programming counters
        prog_summary = next(s for s in summaries if s["name"] == "Programming")
        assert len(prog_summary["counter_totals"]) == 2
        counter_names = {c["name"] for c in prog_summary["counter_totals"]}
        assert counter_names == {"Hours", "Projects"}
        
        # Check Fitness counters
        fitness_summary = next(s for s in summaries if s["name"] == "Fitness")
        assert len(fitness_summary["counter_totals"]) == 2
        counter_names = {c["name"] for c in fitness_summary["counter_totals"]}
        assert counter_names == {"Workouts", "Hours"}
    
    def test_roots_summary_complex_trees(self):
        """Test roots summary with complex multi-level trees."""
        # Create first tree:
        #       Root1
        #      /     \
        #    A        B
        #   / \      / \
        #  C   D    E   F
        
        root1 = client.post("/api/skills/", json={"name": "Root1"}).json()
        a = client.post(f"/api/skills/{root1['id']}/children", json={"name": "A"}).json()
        b = client.post(f"/api/skills/{root1['id']}/children", json={"name": "B"}).json()
        c = client.post(f"/api/skills/{a['id']}/children", json={"name": "C"}).json()
        d = client.post(f"/api/skills/{a['id']}/children", json={"name": "D"}).json()
        e = client.post(f"/api/skills/{b['id']}/children", json={"name": "E"}).json()
        f = client.post(f"/api/skills/{b['id']}/children", json={"name": "F"}).json()
        
        # Create second tree:
        #    Root2
        #      |
        #      G
        #      |
        #      H
        
        root2 = client.post("/api/skills/", json={"name": "Root2"}).json()
        g = client.post(f"/api/skills/{root2['id']}/children", json={"name": "G"}).json()
        h = client.post(f"/api/skills/{g['id']}/children", json={"name": "H"}).json()
        
        # Add counters to leaf nodes in first tree
        for skill_id in [c['id'], d['id'], e['id'], f['id']]:
            client.post(f"/api/counters/?skill_id={skill_id}", json={
                "name": "Value",
                "value": 10
            })
        
        # Add counter to leaf node in second tree
        client.post(f"/api/counters/?skill_id={h['id']}", json={
            "name": "Value",
            "value": 50
        })
        
        # Get roots summary
        response = client.get("/api/skills/roots/summary")
        summaries = response.json()
        
        assert len(summaries) == 2
        
        # Check Root1
        root1_summary = next(s for s in summaries if s["name"] == "Root1")
        assert root1_summary["total_descendants"] == 6  # A, B, C, D, E, F
        assert root1_summary["direct_children_count"] == 2  # A, B
        assert root1_summary["counter_totals"][0]["total"] == 40.0  # 4 * 10
        assert root1_summary["counter_totals"][0]["count"] == 4
        
        # Check Root2
        root2_summary = next(s for s in summaries if s["name"] == "Root2")
        assert root2_summary["total_descendants"] == 2  # G, H
        assert root2_summary["direct_children_count"] == 1  # G
        assert root2_summary["counter_totals"][0]["total"] == 50.0
        assert root2_summary["counter_totals"][0]["count"] == 1
    
    def test_roots_summary_only_returns_roots(self):
        """Test that only root skills are returned, not child skills."""
        # Create hierarchy: Root > Child > Grandchild
        root = client.post("/api/skills/", json={"name": "Root"}).json()
        child = client.post(f"/api/skills/{root['id']}/children", json={"name": "Child"}).json()
        grandchild = client.post(f"/api/skills/{child['id']}/children", json={"name": "Grandchild"}).json()
        
        # Get roots summary
        response = client.get("/api/skills/roots/summary")
        summaries = response.json()
        
        # Only root should be returned
        assert len(summaries) == 1
        assert summaries[0]["name"] == "Root"
        assert summaries[0]["id"] == root["id"]
        
        # Child and grandchild should be in nested structure, not as separate roots
        returned_ids = {summaries[0]["id"]}
        assert child["id"] not in returned_ids
        assert grandchild["id"] not in returned_ids
    
    def test_roots_summary_aggregation_isolated_by_tree(self):
        """Test that counter aggregation is isolated per root tree."""
        # Create two separate trees
        root1 = client.post("/api/skills/", json={"name": "Tree1"}).json()
        root1_child = client.post(f"/api/skills/{root1['id']}/children", json={"name": "Tree1Child"}).json()
        
        root2 = client.post("/api/skills/", json={"name": "Tree2"}).json()
        root2_child = client.post(f"/api/skills/{root2['id']}/children", json={"name": "Tree2Child"}).json()
        
        # Add counters
        client.post(f"/api/counters/?skill_id={root1['id']}", json={
            "name": "Hours",
            "value": 10
        })
        client.post(f"/api/counters/?skill_id={root1_child['id']}", json={
            "name": "Hours",
            "value": 5
        })
        
        client.post(f"/api/counters/?skill_id={root2['id']}", json={
            "name": "Hours",
            "value": 20
        })
        client.post(f"/api/counters/?skill_id={root2_child['id']}", json={
            "name": "Hours",
            "value": 8
        })
        
        # Get roots summary
        response = client.get("/api/skills/roots/summary")
        summaries = response.json()
        
        # Check each tree has its own aggregation
        tree1_summary = next(s for s in summaries if s["name"] == "Tree1")
        assert tree1_summary["counter_totals"][0]["total"] == 15.0  # 10 + 5
        
        tree2_summary = next(s for s in summaries if s["name"] == "Tree2")
        assert tree2_summary["counter_totals"][0]["total"] == 28.0  # 20 + 8
        
        # Totals should NOT be mixed between trees
        assert tree1_summary["counter_totals"][0]["total"] != 43.0
        assert tree2_summary["counter_totals"][0]["total"] != 43.0
    
    def test_roots_summary_with_decimal_values(self):
        """Test roots summary correctly handles decimal counter values."""
        root = client.post("/api/skills/", json={"name": "Root"}).json()
        
        # Add counters with decimals
        client.post(f"/api/counters/?skill_id={root['id']}", json={
            "name": "Hours",
            "value": 1.5
        })
        client.post(f"/api/counters/?skill_id={root['id']}", json={
            "name": "Hours",
            "value": 2.75
        })
        client.post(f"/api/counters/?skill_id={root['id']}", json={
            "name": "Hours",
            "value": 0.25
        })
        
        # Get roots summary
        response = client.get("/api/skills/roots/summary")
        summaries = response.json()
        
        assert len(summaries) == 1
        assert summaries[0]["counter_totals"][0]["total"] == 4.5  # 1.5 + 2.75 + 0.25
        assert summaries[0]["counter_totals"][0]["count"] == 3
