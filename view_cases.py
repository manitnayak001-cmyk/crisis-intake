
from database import init_db, get_case, list_cases

init_db()

print("=== SAVED CASES ===")

for saved_case in list_cases():
    print(f"\nCase ID: {saved_case['id']}")
    print(f"Created at: {saved_case['created_at']}")
    print(f"Incident: {saved_case['case']['incident_type']}")
    print(f"Location: {saved_case['case']['location']}")
    print(f"Status: {saved_case['case']['status']}")

print("\n=== RETRIEVE CASE BY ID ===")

case = get_case(1)

if case:
    print(case)
else:
    print("No case found with ID 1.")
