"""Test counter aggregation with the user's JSON structure."""
import requests
import json

BASE_URL = "http://localhost:10000"

# Load test data
with open("test_import.json", "r") as f:
    test_data = json.load(f)

# Clear existing data
print("Clearing existing data...")
response = requests.delete(f"{BASE_URL}/api/data")
print(f"Clear status: {response.status_code}")

# Import the test data
print("\nImporting test data...")
response = requests.put(f"{BASE_URL}/api/import", json=test_data)
print(f"Import status: {response.status_code}")
if response.status_code == 200:
    imported = response.json()
    print(f"Imported {len(imported)} trees")
    parent_id = imported[0]["id"]
    print(f"Parent skill ID: {parent_id}")
else:
    print(f"Import failed: {response.text}")
    exit(1)

# Get the skill summary for the parent
print(f"\nGetting summary for skill {parent_id}...")
response = requests.get(f"{BASE_URL}/api/skills/{parent_id}/summary")
print(f"Summary status: {response.status_code}")

if response.status_code == 200:
    summary = response.json()
    print(f"\nSkill: {summary['name']}")
    print(f"Total descendants: {summary['total_descendants']}")
    print(f"Direct children: {summary['direct_children_count']}")
    print("\nCounter Totals:")
    for counter in summary['counter_totals']:
        print(f"  {counter['name']}: {counter['total']} / {counter['target']} {counter['unit']} (from {counter['count']} counters)")
    
    print("\nExpected:")
    print("  Questions: 0.0 / 100 count (from 3 counters)")
    print("  Hours: 0.0 / 75.0 hours (from 3 counters)")
    
    # Verify
    questions = next((c for c in summary['counter_totals'] if c['name'] == 'Questions'), None)
    hours = next((c for c in summary['counter_totals'] if c['name'] == 'Hours'), None)
    
    if questions and questions['target'] == 100:
        print("\n✅ Questions target is correct: 100")
    else:
        print(f"\n❌ Questions target is WRONG: {questions['target'] if questions else 'NOT FOUND'}")
    
    if hours and hours['target'] == 75:
        print("✅ Hours target is correct: 75")
    else:
        print(f"❌ Hours target is WRONG: {hours['target'] if hours else 'NOT FOUND'}")
else:
    print(f"Failed to get summary: {response.text}")
