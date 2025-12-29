"""Tests for skill summary endpoint."""
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


class TestGetSkillSummary:
    """Tests for GET /api/skills/{id}/summary endpoint."""
    
    def test_summary_single_skill_no_counters(self):
        """Test summary for a single skill with no counters."""
        # Create a skill
        response = client.post("/api/skills/", json={"name": "Python"})
        assert response.status_code == 201
        skill_id = response.json()["id"]
        
        # Get summary
        response = client.get(f"/api/skills/{skill_id}/summary")
        assert response.status_code == 200
        
        summary = response.json()
        assert summary["id"] == skill_id
        assert summary["name"] == "Python"
        assert summary["parent_id"] is None
        assert summary["counter_totals"] == []
        assert summary["total_descendants"] == 0
        assert summary["direct_children_count"] == 0
        assert summary["children"] == []
    
    def test_summary_skill_with_direct_counters(self):
        """Test summary for a skill with direct counters."""
        # Create skill
        response = client.post("/api/skills/", json={"name": "Python"})
        skill_id = response.json()["id"]
        
        # Add counters
        client.post(f"/api/counters/?skill_id={skill_id}", json={
            "name": "Hours",
            "unit": "h",
            "value": 10.5
        })
        client.post(f"/api/counters/?skill_id={skill_id}", json={
            "name": "Exercises",
            "unit": "count",
            "value": 25
        })
        
        # Get summary
        response = client.get(f"/api/skills/{skill_id}/summary")
        assert response.status_code == 200
        
        summary = response.json()
        assert len(summary["counter_totals"]) == 2
        
        # Check Hours counter
        hours = next(c for c in summary["counter_totals"] if c["name"] == "Hours")
        assert hours["unit"] == "h"
        assert hours["total"] == 10.5
        assert hours["count"] == 1
        
        # Check Exercises counter
        exercises = next(c for c in summary["counter_totals"] if c["name"] == "Exercises")
        assert exercises["unit"] == "count"
        assert exercises["total"] == 25.0
        assert exercises["count"] == 1
    
    def test_summary_with_children_no_counters(self):
        """Test summary for skill with children but no counters."""
        # Create parent
        parent = client.post("/api/skills/", json={"name": "Programming"}).json()
        
        # Create children
        child1 = client.post(f"/api/skills/{parent['id']}/children", json={"name": "Python"}).json()
        child2 = client.post(f"/api/skills/{parent['id']}/children", json={"name": "JavaScript"}).json()
        print(child1, child2)
        
        # Get summary
        response = client.get(f"/api/skills/{parent['id']}/summary")
        assert response.status_code == 200
        
        summary = response.json()
        assert summary["total_descendants"] == 2
        assert summary["direct_children_count"] == 2
        assert len(summary["children"]) == 2
        assert summary["counter_totals"] == []
        
        # Check children names
        child_names = {c["name"] for c in summary["children"]}
        assert child_names == {"Python", "JavaScript"}
    
    def test_summary_aggregates_child_counters(self):
        """Test that summary aggregates counters from children."""
        # Create hierarchy: Programming > Python > Django
        parent = client.post("/api/skills/", json={"name": "Programming"}).json()
        child = client.post(f"/api/skills/{parent['id']}/children", json={"name": "Python"}).json()
        grandchild = client.post(f"/api/skills/{child['id']}/children", json={"name": "Django"}).json()
        
        # Add counters at different levels
        client.post(f"/api/counters/?skill_id={parent['id']}", json={
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
        
        # Get parent summary
        response = client.get(f"/api/skills/{parent['id']}/summary")
        assert response.status_code == 200
        
        summary = response.json()
        assert len(summary["counter_totals"]) == 1
        
        hours = summary["counter_totals"][0]
        assert hours["name"] == "Hours"
        assert hours["unit"] == "h"
        assert hours["total"] == 18.5  # 5 + 10 + 3.5
        assert hours["count"] == 3
    
    def test_summary_aggregates_multiple_counter_types(self):
        """Test aggregation of multiple counter types across hierarchy."""
        # Create hierarchy
        parent = client.post("/api/skills/", json={"name": "Web Dev"}).json()
        child1 = client.post(f"/api/skills/{parent['id']}/children", json={"name": "Frontend"}).json()
        child2 = client.post(f"/api/skills/{parent['id']}/children", json={"name": "Backend"}).json()
        
        # Add various counters
        client.post(f"/api/counters/?skill_id={parent['id']}", json={
            "name": "Projects",
            "unit": "count",
            "value": 2
        })
        client.post(f"/api/counters/?skill_id={child1['id']}", json={
            "name": "Projects",
            "unit": "count",
            "value": 5
        })
        client.post(f"/api/counters/?skill_id={child1['id']}", json={
            "name": "Hours",
            "unit": "h",
            "value": 20
        })
        client.post(f"/api/counters/?skill_id={child2['id']}", json={
            "name": "Projects",
            "unit": "count",
            "value": 3
        })
        client.post(f"/api/counters/?skill_id={child2['id']}", json={
            "name": "Hours",
            "unit": "h",
            "value": 15
        })
        
        # Get parent summary
        response = client.get(f"/api/skills/{parent['id']}/summary")
        summary = response.json()
        
        assert len(summary["counter_totals"]) == 2
        
        projects = next(c for c in summary["counter_totals"] if c["name"] == "Projects")
        assert projects["total"] == 10.0  # 2 + 5 + 3
        assert projects["count"] == 3
        
        hours = next(c for c in summary["counter_totals"] if c["name"] == "Hours")
        assert hours["total"] == 35.0  # 20 + 15
        assert hours["count"] == 2
    
    def test_summary_deep_hierarchy(self):
        """Test summary with deep skill hierarchy."""
        # Create deep hierarchy: A > B > C > D
        a = client.post("/api/skills/", json={"name": "A"}).json()
        b = client.post(f"/api/skills/{a['id']}/children", json={"name": "B"}).json()
        c = client.post(f"/api/skills/{b['id']}/children", json={"name": "C"}).json()
        d = client.post(f"/api/skills/{c['id']}/children", json={"name": "D"}).json()
        
        # Add counter at deepest level
        client.post(f"/api/counters/?skill_id={d['id']}", json={
            "name": "Count",
            "value": 100
        })
        
        # Get root summary
        response = client.get(f"/api/skills/{a['id']}/summary")
        summary = response.json()
        
        assert summary["total_descendants"] == 3  # B, C, D
        assert summary["direct_children_count"] == 1  # Only B
        assert len(summary["counter_totals"]) == 1
        assert summary["counter_totals"][0]["total"] == 100.0
        
        # Check nested children structure
        assert len(summary["children"]) == 1
        assert summary["children"][0]["name"] == "B"
        assert len(summary["children"][0]["children"]) == 1
        assert summary["children"][0]["children"][0]["name"] == "C"
    
    def test_summary_counters_without_unit(self):
        """Test summary with counters that have no unit."""
        # Create skill
        skill = client.post("/api/skills/", json={"name": "Skill"}).json()
        
        # Add counter without unit
        client.post(f"/api/counters/?skill_id={skill['id']}", json={
            "name": "Progress",
            "value": 42
        })
        
        # Get summary
        response = client.get(f"/api/skills/{skill['id']}/summary")
        summary = response.json()
        
        assert len(summary["counter_totals"]) == 1
        assert summary["counter_totals"][0]["name"] == "Progress"
        assert summary["counter_totals"][0]["unit"] is None
        assert summary["counter_totals"][0]["total"] == 42.0
    
    def test_summary_multiple_counters_same_name_different_units(self):
        """Test that counters with same name but different units are kept separate."""
        # Create parent and children
        parent = client.post("/api/skills/", json={"name": "Parent"}).json()
        child1 = client.post(f"/api/skills/{parent['id']}/children", json={"name": "Child1"}).json()
        child2 = client.post(f"/api/skills/{parent['id']}/children", json={"name": "Child2"}).json()
        
        # Add counters with same name but different units
        client.post(f"/api/counters/?skill_id={child1['id']}", json={
            "name": "Practice",
            "unit": "hours",
            "value": 10
        })
        client.post(f"/api/counters/?skill_id={child2['id']}", json={
            "name": "Practice",
            "unit": "days",
            "value": 5
        })
        
        # Get summary
        response = client.get(f"/api/skills/{parent['id']}/summary")
        summary = response.json()
        
        assert len(summary["counter_totals"]) == 2
        
        hours = next(c for c in summary["counter_totals"] if c["unit"] == "hours")
        assert hours["total"] == 10.0
        
        days = next(c for c in summary["counter_totals"] if c["unit"] == "days")
        assert days["total"] == 5.0
    
    def test_summary_nonexistent_skill(self):
        """Test summary for skill that doesn't exist."""
        response = client.get("/api/skills/99999/summary")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_summary_child_only_includes_its_descendants(self):
        """Test that child summary only includes its own descendants."""
        # Create hierarchy: Root > [Child1 > GrandChild1, Child2]
        root = client.post("/api/skills/", json={"name": "Root"}).json()
        child1 = client.post(f"/api/skills/{root['id']}/children", json={"name": "Child1"}).json()
        child2 = client.post(f"/api/skills/{root['id']}/children", json={"name": "Child2"}).json()
        grandchild1 = client.post(f"/api/skills/{child1['id']}/children", json={"name": "GrandChild1"}).json()
        
        # Add counters
        client.post(f"/api/counters/?skill_id={child1['id']}", json={"name": "Count", "value": 10})
        client.post(f"/api/counters/?skill_id={grandchild1['id']}", json={"name": "Count", "value": 5})
        client.post(f"/api/counters/?skill_id={child2['id']}", json={"name": "Count", "value": 20})
        
        # Get Child1 summary - should include GrandChild1 but not Child2
        response = client.get(f"/api/skills/{child1['id']}/summary")
        summary = response.json()
        
        assert summary["total_descendants"] == 1  # Only GrandChild1
        assert summary["direct_children_count"] == 1
        assert summary["counter_totals"][0]["total"] == 15.0  # 10 + 5, not including Child2's 20
        assert summary["counter_totals"][0]["count"] == 2
    
    def test_summary_with_decimal_counter_values(self):
        """Test summary correctly handles decimal counter values."""
        # Create skill
        skill = client.post("/api/skills/", json={"name": "Skill"}).json()
        
        # Add counters with decimals
        client.post(f"/api/counters/?skill_id={skill['id']}", json={
            "name": "Hours",
            "value": 1.5
        })
        client.post(f"/api/counters/?skill_id={skill['id']}", json={
            "name": "Hours",
            "value": 2.75
        })
        
        # Get summary
        response = client.get(f"/api/skills/{skill['id']}/summary")
        summary = response.json()
        
        assert summary["counter_totals"][0]["total"] == 4.25
        assert summary["counter_totals"][0]["count"] == 2
    
    def test_summary_complex_tree_structure(self):
        """Test summary with complex tree structure (multiple branches)."""
        # Create tree:
        #       Root
        #      /    \
        #    A       B
        #   / \     / \
        #  C   D   E   F
        
        root = client.post("/api/skills/", json={"name": "Root"}).json()
        a = client.post(f"/api/skills/{root['id']}/children", json={"name": "A"}).json()
        b = client.post(f"/api/skills/{root['id']}/children", json={"name": "B"}).json()
        c = client.post(f"/api/skills/{a['id']}/children", json={"name": "C"}).json()
        d = client.post(f"/api/skills/{a['id']}/children", json={"name": "D"}).json()
        e = client.post(f"/api/skills/{b['id']}/children", json={"name": "E"}).json()
        f = client.post(f"/api/skills/{b['id']}/children", json={"name": "F"}).json()
        
        # Add counters at leaf nodes
        for skill_id in [c['id'], d['id'], e['id'], f['id']]:
            client.post(f"/api/counters/?skill_id={skill_id}", json={
                "name": "Value",
                "value": 10
            })
        
        # Get root summary
        response = client.get(f"/api/skills/{root['id']}/summary")
        summary = response.json()
        
        assert summary["total_descendants"] == 6  # A, B, C, D, E, F
        assert summary["direct_children_count"] == 2  # A, B
        assert summary["counter_totals"][0]["total"] == 40.0  # 4 * 10
        assert summary["counter_totals"][0]["count"] == 4
        
        # Verify children structure
        assert len(summary["children"]) == 2
        for child in summary["children"]:
            assert child["direct_children_count"] == 2
            assert len(child["children"]) == 2


class TestCounterTargetAggregation:
    """Tests for counter target aggregation in summaries."""

    def test_summary_aggregates_targets_from_children(self):
        """Test that summary aggregates target values from parent and all children."""
        # Create hierarchy: Programming > Python > Django
        parent = client.post("/api/skills/", json={"name": "Programming"}).json()
        child = client.post(f"/api/skills/{parent['id']}/children", json={"name": "Python"}).json()
        grandchild = client.post(f"/api/skills/{child['id']}/children", json={"name": "Django"}).json()
        
        # Add counters with targets at different levels
        client.post(f"/api/counters/?skill_id={parent['id']}", json={
            "name": "Videos",
            "value": 5.0,
            "target": 20.0
        })
        client.post(f"/api/counters/?skill_id={child['id']}", json={
            "name": "Videos",
            "value": 10.0,
            "target": 50.0
        })
        client.post(f"/api/counters/?skill_id={grandchild['id']}", json={
            "name": "Videos",
            "value": 3.5,
            "target": 30.0
        })
        
        # Get parent summary
        response = client.get(f"/api/skills/{parent['id']}/summary")
        assert response.status_code == 200
        
        summary = response.json()
        assert len(summary["counter_totals"]) == 1
        
        videos = summary["counter_totals"][0]
        assert videos["name"] == "Videos"
        assert videos["total"] == 18.5  # 5 + 10 + 3.5
        assert videos["target"] == 100.0  # 20 + 50 + 30
        assert videos["count"] == 3

    def test_summary_aggregates_targets_across_siblings(self):
        """Test that targets are summed across sibling skills."""
        # Create hierarchy with multiple children
        parent = client.post("/api/skills/", json={"name": "AWS Course"}).json()
        section1 = client.post(f"/api/skills/{parent['id']}/children", json={"name": "Section 1"}).json()
        section2 = client.post(f"/api/skills/{parent['id']}/children", json={"name": "Section 2"}).json()
        section3 = client.post(f"/api/skills/{parent['id']}/children", json={"name": "Section 3"}).json()
        
        # Add counters to each section
        client.post(f"/api/counters/?skill_id={section1['id']}", json={
            "name": "Videos",
            "value": 0,
            "target": 50
        })
        client.post(f"/api/counters/?skill_id={section2['id']}", json={
            "name": "Videos",
            "value": 0,
            "target": 100
        })
        client.post(f"/api/counters/?skill_id={section3['id']}", json={
            "name": "Videos",
            "value": 0,
            "target": 119
        })
        
        # Get parent summary
        response = client.get(f"/api/skills/{parent['id']}/summary")
        summary = response.json()
        
        videos = summary["counter_totals"][0]
        assert videos["name"] == "Videos"
        assert videos["total"] == 0
        assert videos["target"] == 269  # 50 + 100 + 119
        assert videos["count"] == 3

    def test_summary_multiple_counter_types_with_targets(self):
        """Test aggregation of multiple counter types with different targets."""
        parent = client.post("/api/skills/", json={"name": "Course"}).json()
        child1 = client.post(f"/api/skills/{parent['id']}/children", json={"name": "Module 1"}).json()
        child2 = client.post(f"/api/skills/{parent['id']}/children", json={"name": "Module 2"}).json()
        
        # Add various counter types with targets
        client.post(f"/api/counters/?skill_id={child1['id']}", json={
            "name": "Videos",
            "value": 5,
            "target": 50
        })
        client.post(f"/api/counters/?skill_id={child1['id']}", json={
            "name": "Quizzes",
            "value": 2,
            "target": 10
        })
        client.post(f"/api/counters/?skill_id={child1['id']}", json={
            "name": "Duration",
            "unit": "Mins",
            "value": 120,
            "target": 300
        })
        client.post(f"/api/counters/?skill_id={child2['id']}", json={
            "name": "Videos",
            "value": 8,
            "target": 40
        })
        client.post(f"/api/counters/?skill_id={child2['id']}", json={
            "name": "Quizzes",
            "value": 1,
            "target": 8
        })
        client.post(f"/api/counters/?skill_id={child2['id']}", json={
            "name": "Duration",
            "unit": "Mins",
            "value": 200,
            "target": 400
        })
        
        # Get parent summary
        response = client.get(f"/api/skills/{parent['id']}/summary")
        summary = response.json()
        
        assert len(summary["counter_totals"]) == 3
        
        videos = next(c for c in summary["counter_totals"] if c["name"] == "Videos")
        assert videos["total"] == 13  # 5 + 8
        assert videos["target"] == 90  # 50 + 40
        assert videos["count"] == 2
        
        quizzes = next(c for c in summary["counter_totals"] if c["name"] == "Quizzes")
        assert quizzes["total"] == 3  # 2 + 1
        assert quizzes["target"] == 18  # 10 + 8
        assert quizzes["count"] == 2
        
        duration = next(c for c in summary["counter_totals"] if c["name"] == "Duration")
        assert duration["total"] == 320  # 120 + 200
        assert duration["target"] == 700  # 300 + 400
        assert duration["unit"] == "Mins"
        assert duration["count"] == 2

    def test_summary_counters_with_null_targets(self):
        """Test that counters with null targets are handled correctly."""
        parent = client.post("/api/skills/", json={"name": "Parent"}).json()
        child1 = client.post(f"/api/skills/{parent['id']}/children", json={"name": "Child1"}).json()
        child2 = client.post(f"/api/skills/{parent['id']}/children", json={"name": "Child2"}).json()
        
        # One with target, one without
        client.post(f"/api/counters/?skill_id={child1['id']}", json={
            "name": "Projects",
            "value": 5,
            "target": 10
        })
        client.post(f"/api/counters/?skill_id={child2['id']}", json={
            "name": "Projects",
            "value": 3,
            "target": None
        })
        
        response = client.get(f"/api/skills/{parent['id']}/summary")
        summary = response.json()
        
        projects = summary["counter_totals"][0]
        assert projects["total"] == 8  # 5 + 3
        assert projects["target"] == 10  # Only child1's target
        assert projects["count"] == 2

    def test_summary_all_null_targets_returns_none(self):
        """Test that when all targets are null, aggregated target is None."""
        parent = client.post("/api/skills/", json={"name": "Parent"}).json()
        child1 = client.post(f"/api/skills/{parent['id']}/children", json={"name": "Child1"}).json()
        child2 = client.post(f"/api/skills/{parent['id']}/children", json={"name": "Child2"}).json()
        
        # Both without targets
        client.post(f"/api/counters/?skill_id={child1['id']}", json={
            "name": "Notes",
            "value": 5
        })
        client.post(f"/api/counters/?skill_id={child2['id']}", json={
            "name": "Notes",
            "value": 3
        })
        
        response = client.get(f"/api/skills/{parent['id']}/summary")
        summary = response.json()
        
        notes = summary["counter_totals"][0]
        assert notes["total"] == 8
        assert notes["target"] is None
        assert notes["count"] == 2

    def test_summary_deep_hierarchy_target_aggregation(self):
        """Test target aggregation works correctly in deep hierarchies."""
        # Create deep hierarchy: Root > L1 > L2 > L3
        root = client.post("/api/skills/", json={"name": "Root"}).json()
        l1 = client.post(f"/api/skills/{root['id']}/children", json={"name": "Level1"}).json()
        l2 = client.post(f"/api/skills/{l1['id']}/children", json={"name": "Level2"}).json()
        l3 = client.post(f"/api/skills/{l2['id']}/children", json={"name": "Level3"}).json()
        
        # Add counters at each level
        client.post(f"/api/counters/?skill_id={root['id']}", json={
            "name": "Sections",
            "value": 1,
            "target": 5
        })
        client.post(f"/api/counters/?skill_id={l1['id']}", json={
            "name": "Sections",
            "value": 2,
            "target": 8
        })
        client.post(f"/api/counters/?skill_id={l2['id']}", json={
            "name": "Sections",
            "value": 0,
            "target": 6
        })
        client.post(f"/api/counters/?skill_id={l3['id']}", json={
            "name": "Sections",
            "value": 0,
            "target": 4
        })
        
        # Get root summary - should aggregate all
        response = client.get(f"/api/skills/{root['id']}/summary")
        summary = response.json()
        
        sections = summary["counter_totals"][0]
        assert sections["total"] == 3  # 1 + 2 + 0 + 0
        assert sections["target"] == 23  # 5 + 8 + 6 + 4
        assert sections["count"] == 4
        
        # Get L1 summary - should not include root's counter
        response_l1 = client.get(f"/api/skills/{l1['id']}/summary")
        summary_l1 = response_l1.json()
        
        sections_l1 = summary_l1["counter_totals"][0]
        assert sections_l1["total"] == 2  # 2 + 0 + 0
        assert sections_l1["target"] == 18  # 8 + 6 + 4 (no root's 5)
        assert sections_l1["count"] == 3
