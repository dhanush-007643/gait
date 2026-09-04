import sys
import uuid
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(_ROOT / "app"))
sys.path.insert(0, str(_ROOT / "src"))
sys.path.insert(0, str(_ROOT / "db"))

from app import app
client = app.test_client()

print("1. Testing /health...")
r = client.get("/health")
print("Status:", r.status_code, r.get_json())
assert r.status_code == 200

print("\n2. Testing /api/model/performance...")
r = client.get("/api/model/performance")
print("Status:", r.status_code, r.get_json().get("metrics"))
assert r.status_code == 200

print("\n3. Testing /api/auth/register with admin role...")
random_email = f"admin_{uuid.uuid4().hex[:8]}@gaitinsight.dev"
r = client.post("/api/auth/register", json={
    "name": "System Administrator",
    "email": random_email,
    "password": "adminpassword123",
    "role": "admin"
})
print("Status:", r.status_code, r.get_json())
assert r.status_code == 201

print("\n4. Testing /api/auth/login with demo credentials...")
r = client.post("/api/auth/login", json={"email": "demo@gaitinsight.dev", "password": "demo1234"})
print("Status:", r.status_code, r.get_json())
assert r.status_code == 200
headers = {"Authorization": "Bearer " + r.get_json()["access_token"]}

print("\n5. Testing /api/users/me...")
r = client.get("/api/users/me", headers=headers)
print("Status:", r.status_code, r.get_json())
assert r.status_code == 200

print("\n6. Testing /api/dashboard/summary...")
r = client.get("/api/dashboard/summary", headers=headers)
print("Status:", r.status_code, r.get_json())
assert r.status_code == 200

print("\n7. Testing /api/subjects...")
r = client.get("/api/subjects", headers=headers)
print("Status:", r.status_code, "Subjects count:", len(r.get_json()))
assert r.status_code == 200

print("\n8. Testing /api/gait/upload with raw CSV...")
csv_path = _ROOT / "data" / "raw" / "subject_00_normal_10.csv"
with open(csv_path, "rb") as f_in:
    r = client.post("/api/gait/upload", data={"file": (f_in, "subject_00_normal_10.csv"), "sampling_rate": 100.0}, headers=headers)
print("Status:", r.status_code, r.get_json())
assert r.status_code == 201
res = r.get_json()
session_id = res["session_id"]

print("\n9. Testing /api/gait/sessions...")
r = client.get("/api/gait/sessions", headers=headers)
print("Status:", r.status_code, "Total sessions:", r.get_json()["total"])
assert r.status_code == 200

print(f"\n10. Testing /api/gait/sessions/{session_id}...")
r = client.get(f"/api/gait/sessions/{session_id}", headers=headers)
print("Status:", r.status_code, "Predicted:", r.get_json()["prediction"]["predicted_class"])
assert r.status_code == 200

print("\n11. Testing /predict/features endpoint...")
features = res["features"]
r = client.post("/predict/features", json=features, headers=headers)
print("Status:", r.status_code, r.get_json())
assert r.status_code == 200
assert "predicted_class" in r.get_json()
assert "probabilities" in r.get_json()

print("\n12. Testing /api/gait/stream/simulate...")
r = client.get("/api/gait/stream/simulate?points=10", headers=headers)
print("Status:", r.status_code, "Points count:", len(r.get_json()["points"]))
assert r.status_code == 200

print(f"\n13. Testing /api/gait/sessions/{session_id} DELETE...")
r = client.delete(f"/api/gait/sessions/{session_id}", headers=headers)
print("Status:", r.status_code, r.get_json())
assert r.status_code == 200

print("\nALL 13 TESTS PASSED WITH 100 PERCENT SUCCESS!")
