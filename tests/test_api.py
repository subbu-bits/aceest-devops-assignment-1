"""Tests for the Flask API endpoints."""


# ---------------- General ----------------
def test_home(client):
    res = client.get("/")
    assert res.status_code == 200
    assert res.get_json()["status"] == "running"


def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.get_json() == {"status": "healthy"}


# ---------------- Programs ----------------
def test_list_programs(client):
    data = client.get("/programs").get_json()
    assert set(data.keys()) == {"FL", "MG", "BG"}


def test_get_program_case_insensitive(client):
    res = client.get("/programs/fl")
    assert res.status_code == 200
    body = res.get_json()
    assert body["name"] == "Fat Loss"
    assert body["calorie_factor"] == 22
    assert len(body["workout"]) > 0


def test_get_program_not_found(client):
    assert client.get("/programs/XX").status_code == 404


# ---------------- Calculators ----------------
def test_calories_endpoint(client):
    res = client.post("/calories", json={"weight": 80, "program": "FL"})
    assert res.status_code == 200
    assert res.get_json()["calories"] == 1760


def test_calories_bad_program(client):
    res = client.post("/calories", json={"weight": 80, "program": "ZZ"})
    assert res.status_code == 400


def test_calories_no_body(client):
    assert client.post("/calories").status_code == 400


def test_bmi_endpoint(client):
    res = client.post("/bmi", json={"weight": 70, "height": 175})
    assert res.status_code == 200
    assert res.get_json() == {"bmi": 22.9, "category": "Normal"}


def test_bmi_invalid(client):
    res = client.post("/bmi", json={"weight": 70, "height": 0})
    assert res.status_code == 400


# ---------------- Clients ----------------
def test_create_client(client):
    res = client.post("/clients", json={
        "name": "Priya", "age": 25, "weight": 60, "program": "FL"})
    assert res.status_code == 201
    body = res.get_json()
    assert body["name"] == "Priya"
    assert body["calories"] == 1320  # 60 x 22
    assert body["membership_status"] == "Active"


def test_create_client_missing_name(client):
    res = client.post("/clients", json={"weight": 60, "program": "FL"})
    assert res.status_code == 400


def test_create_client_invalid_program(client):
    res = client.post("/clients", json={
        "name": "Ravi", "weight": 60, "program": "YOGA"})
    assert res.status_code == 400


def test_create_client_invalid_weight(client):
    res = client.post("/clients", json={
        "name": "Ravi", "weight": 0, "program": "FL"})
    assert res.status_code == 400


def test_create_duplicate_client(client, sample_client):
    res = client.post("/clients", json={
        "name": sample_client, "weight": 70, "program": "MG"})
    assert res.status_code == 409


def test_list_clients(client, sample_client):
    data = client.get("/clients").get_json()
    assert [c["name"] for c in data] == [sample_client]


def test_get_client(client, sample_client):
    res = client.get(f"/clients/{sample_client}")
    assert res.status_code == 200
    assert res.get_json()["calories"] == 2450


def test_get_missing_client(client):
    assert client.get("/clients/Nobody").status_code == 404


def test_delete_client(client, sample_client):
    assert client.delete(f"/clients/{sample_client}").status_code == 200
    assert client.get(f"/clients/{sample_client}").status_code == 404


def test_delete_missing_client(client):
    assert client.delete("/clients/Nobody").status_code == 404


# ---------------- Progress ----------------
def test_add_and_get_progress(client, sample_client):
    url = f"/clients/{sample_client}/progress"
    assert client.post(url, json={"week": "Week 01 - 2026",
                                  "adherence": 80}).status_code == 201
    assert client.post(url, json={"week": "Week 02 - 2026",
                                  "adherence": 90}).status_code == 201
    data = client.get(url).get_json()
    assert [p["adherence"] for p in data] == [80, 90]


def test_progress_invalid_adherence(client, sample_client):
    res = client.post(f"/clients/{sample_client}/progress",
                      json={"week": "Week 01 - 2026", "adherence": 150})
    assert res.status_code == 400


def test_progress_missing_week(client, sample_client):
    res = client.post(f"/clients/{sample_client}/progress",
                      json={"adherence": 50})
    assert res.status_code == 400


def test_progress_unknown_client(client):
    res = client.post("/clients/Nobody/progress",
                      json={"week": "Week 01 - 2026", "adherence": 50})
    assert res.status_code == 404


# ---------------- Workouts ----------------
def test_add_and_get_workouts(client, sample_client):
    url = f"/clients/{sample_client}/workouts"
    res = client.post(url, json={"date": "2026-01-10",
                                 "workout_type": "Strength",
                                 "duration_min": 45})
    assert res.status_code == 201
    data = client.get(url).get_json()
    assert len(data) == 1
    assert data[0]["workout_type"] == "Strength"


def test_workout_invalid_type(client, sample_client):
    res = client.post(f"/clients/{sample_client}/workouts",
                      json={"date": "2026-01-10", "workout_type": "Dancing"})
    assert res.status_code == 400


def test_workout_missing_date(client, sample_client):
    res = client.post(f"/clients/{sample_client}/workouts",
                      json={"workout_type": "Cardio"})
    assert res.status_code == 400


# ---------------- Program generator ----------------
def test_generate_program(client, sample_client):
    res = client.post(f"/clients/{sample_client}/generate-program")
    assert res.status_code == 200
    body = res.get_json()
    assert body["program"] == "MG"
    assert body["suggested_plan"] in [
        "Push/Pull/Legs", "Upper/Lower Split", "Full Body Strength"]


def test_generate_program_unknown_client(client):
    assert client.post(
        "/clients/Nobody/generate-program").status_code == 404
