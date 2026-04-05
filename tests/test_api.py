from decimal import Decimal


def _login(client, email: str, password: str) -> str:
    r = client.post("/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _hdr(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_seed_admin_login(client):
    token = _login(client, "admin@example.com", "Admin12345!")
    assert token


def test_login_invalid(client):
    r = client.post("/auth/login", json={"email": "admin@example.com", "password": "wrong"})
    assert r.status_code == 401


def test_validation_bad_amount(client):
    token = _login(client, "admin@example.com", "Admin12345!")
    r = client.post(
        "/records",
        headers=_hdr(token),
        json={
            "amount": "-10",
            "type": "income",
            "category": "Test",
            "entry_date": "2024-01-15",
        },
    )
    assert r.status_code == 422


def test_rbac_viewer_cannot_list_records(client):
    admin_t = _login(client, "admin@example.com", "Admin12345!")
    cr = client.post(
        "/users",
        headers=_hdr(admin_t),
        json={
            "email": "v@example.com",
            "password": "Viewer12345!",
            "full_name": "V",
            "role": "viewer",
        },
    )
    assert cr.status_code == 201
    vt = _login(client, "v@example.com", "Viewer12345!")
    lr = client.get("/records", headers=_hdr(vt))
    assert lr.status_code == 403


def test_rbac_viewer_can_dashboard(client):
    admin_t = _login(client, "admin@example.com", "Admin12345!")
    client.post(
        "/users",
        headers=_hdr(admin_t),
        json={
            "email": "v2@example.com",
            "password": "Viewer12345!",
            "full_name": "V2",
            "role": "viewer",
        },
    )
    vt = _login(client, "v2@example.com", "Viewer12345!")
    s = client.get("/dashboard/summary", headers=_hdr(vt))
    assert s.status_code == 200
    body = s.json()
    assert "total_income" in body
    assert body["record_count"] == 0


def test_admin_crud_and_analyst_read(client):
    admin_t = _login(client, "admin@example.com", "Admin12345!")
    client.post(
        "/users",
        headers=_hdr(admin_t),
        json={
            "email": "a@example.com",
            "password": "Analyst12345!",
            "full_name": "Analyst",
            "role": "analyst",
        },
    )
    pr = client.post(
        "/records",
        headers=_hdr(admin_t),
        json={
            "amount": "100.50",
            "type": "income",
            "category": "Salary",
            "entry_date": "2024-02-01",
            "notes": "Monthly",
        },
    )
    assert pr.status_code == 201
    rid = pr.json()["id"]

    at = _login(client, "a@example.com", "Analyst12345!")
    gr = client.get(f"/records/{rid}", headers=_hdr(at))
    assert gr.status_code == 200
    assert Decimal(gr.json()["amount"]) == Decimal("100.50")

    ur = client.patch(
        f"/records/{rid}",
        headers=_hdr(at),
        json={"notes": "nope"},
    )
    assert ur.status_code == 403

    summ = client.get("/dashboard/summary", headers=_hdr(at))
    assert summ.status_code == 200
    assert summ.json()["total_income"] == "100.50"


def test_soft_delete_hides_record(client):
    admin_t = _login(client, "admin@example.com", "Admin12345!")
    pr = client.post(
        "/records",
        headers=_hdr(admin_t),
        json={
            "amount": "10.00",
            "type": "expense",
            "category": "Coffee",
            "entry_date": "2024-03-01",
        },
    )
    rid = pr.json()["id"]
    dr = client.delete(f"/records/{rid}", headers=_hdr(admin_t))
    assert dr.status_code == 204
    gr = client.get(f"/records/{rid}", headers=_hdr(admin_t))
    assert gr.status_code == 404
