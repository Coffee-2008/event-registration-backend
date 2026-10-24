"""Quick checks for every case in the task. Run: python test_app.py"""

import os
import tempfile

os.environ["DB_PATH"] = os.path.join(tempfile.mkdtemp(), "test.db")

import app as backend  # noqa: E402

client = backend.app.test_client()


def register(i, **extra):
    body = {"name": f"Student {i}", "email": f"s{i}@example.com", **extra}
    return client.post("/register", json=body)


# successful registration
r = register(1, college="CIT - AI&DS")
assert r.status_code == 201, r.json
assert r.json["registration"]["id"] == 1

# duplicate (also with different capitals)
r = client.post("/register", json={"name": "X", "email": "S1@Example.com"})
assert r.status_code == 409 and "already" in r.json["error"]

# invalid / missing
assert client.post("/register", json={"email": "a@b.com"}).status_code == 400
assert client.post("/register", json={"name": "A", "email": "nope"}).status_code == 400
assert client.post("/register", data="not json").status_code == 400

# fill up to 50
for i in range(2, 51):
    assert register(i).status_code == 201

# 51st is rejected
r = register(51)
assert r.status_code == 409 and r.json["error"] == "Event is full"

# view all
r = client.get("/registrations")
assert r.json["seats_filled"] == 50 and len(r.json["registrations"]) == 50

# view one (by id and by email), and not found
assert client.get("/registrations/1").json["email"] == "s1@example.com"
assert client.get("/registrations/email/s2@example.com").json["id"] == 2
assert client.get("/registrations/999").status_code == 404
assert client.get("/registrations/email/ghost@example.com").status_code == 404

print("All checks passed")
