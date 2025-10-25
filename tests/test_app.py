import sys
from pathlib import Path

# Ensure the src directory is on the path so we can import the app module
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from fastapi.testclient import TestClient  # type: ignore
from app import app  # noqa: E402

client = TestClient(app)


def test_root_redirect():
    response = client.get("/", allow_redirects=False)
    assert response.status_code in (307, 302)
    assert response.headers.get("location") == "/static/index.html"


def test_get_activities():
    response = client.get("/activities")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    # Spot-check a known activity structure
    assert "Chess Club" in data
    chess = data["Chess Club"]
    assert "description" in chess
    assert "participants" in chess and isinstance(chess["participants"], list)


def test_signup_and_unregister_flow():
    activity = "Chess Club"
    email = "autotest_student@mergington.edu"

    # Ensure cleanup in case of previous run leftovers
    client.post(f"/activities/{activity}/unregister", params={"email": email})

    # Sign up should succeed
    r_signup = client.post(f"/activities/{activity}/signup", params={"email": email})
    assert r_signup.status_code == 200
    assert "Signed up" in r_signup.json().get("message", "")

    # Verify presence
    r_get = client.get("/activities")
    assert r_get.status_code == 200
    assert email in r_get.json()[activity]["participants"]

    # Unregister should succeed
    r_unreg = client.post(f"/activities/{activity}/unregister", params={"email": email})
    assert r_unreg.status_code == 200
    assert "Unregistered" in r_unreg.json().get("message", "")

    # Verify removal
    r_get2 = client.get("/activities")
    assert r_get2.status_code == 200
    assert email not in r_get2.json()[activity]["participants"]


def test_signup_duplicate_rejected():
    activity = "Chess Club"
    # Use an existing seeded participant from app.py
    existing_email = "michael@mergington.edu"
    r = client.post(f"/activities/{activity}/signup", params={"email": existing_email})
    assert r.status_code == 400
    assert "already" in r.json().get("detail", "").lower()


def test_unregister_when_not_registered_rejected():
    activity = "Chess Club"
    email = "not_registered_yet@mergington.edu"
    # Make sure it's not registered
    client.post(f"/activities/{activity}/unregister", params={"email": email})
    r = client.post(f"/activities/{activity}/unregister", params={"email": email})
    assert r.status_code == 400
    assert "not registered" in r.json().get("detail", "").lower()
