import pytest
from datetime import datetime, timedelta

def get_auth_headers(client, email, name="Test User"):
    client.post(
        "/auth/register",
        json={"name": name, "email": email, "password": "password123"}
    )
    login_resp = client.post(
        "/auth/login",
        json={"email": email, "password": "password123"}
    )
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_create_transaction(client):
    headers = get_auth_headers(client, "tx1@example.com")
    
    # Valid transaction
    response = client.post(
        "/transactions/",
        headers=headers,
        json={
            "amount": 150.50,
            "type": "expense",
            "category": "Food",
            "note": "Lunch with team",
            "date": "2026-05-20T12:00:00"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["amount"] == 150.50
    assert data["category"] == "Food"
    assert data["type"] == "expense"
    assert data["note"] == "Lunch with team"
    assert "2026-05-20" in data["date"]

def test_create_transaction_invalid_category(client):
    headers = get_auth_headers(client, "tx2@example.com")
    response = client.post(
        "/transactions/",
        headers=headers,
        json={
            "amount": 50.00,
            "type": "expense",
            "category": "NonExistentCategory",
        }
    )
    assert response.status_code == 400
    assert "not a valid default or custom category" in response.json()["detail"]

def test_create_transaction_negative_amount(client):
    headers = get_auth_headers(client, "tx3@example.com")
    response = client.post(
        "/transactions/",
        headers=headers,
        json={
            "amount": -10.00,
            "type": "expense",
            "category": "Food",
        }
    )
    assert response.status_code == 422 # Pydantic validation error

def test_get_transaction_by_id(client):
    headers = get_auth_headers(client, "tx4@example.com")
    # Create
    create_resp = client.post(
        "/transactions/",
        headers=headers,
        json={"amount": 100, "type": "income", "category": "Other"}
    )
    tx_id = create_resp.json()["id"]

    # Get
    get_resp = client.get(f"/transactions/{tx_id}", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["amount"] == 100.0

def test_transaction_ownership_protection(client):
    headers1 = get_auth_headers(client, "u1@example.com", "User One")
    headers2 = get_auth_headers(client, "u2@example.com", "User Two")

    # User 1 creates transaction
    create_resp = client.post(
        "/transactions/",
        headers=headers1,
        json={"amount": 100, "type": "income", "category": "Other"}
    )
    tx_id = create_resp.json()["id"]

    # User 2 tries to fetch User 1's transaction
    get_resp = client.get(f"/transactions/{tx_id}", headers=headers2)
    assert get_resp.status_code == 404

    # User 2 tries to update User 1's transaction
    patch_resp = client.patch(
        f"/transactions/{tx_id}",
        headers=headers2,
        json={"amount": 200}
    )
    assert patch_resp.status_code == 404

    # User 2 tries to delete User 1's transaction
    delete_resp = client.delete(f"/transactions/{tx_id}", headers=headers2)
    assert delete_resp.status_code == 404

def test_transaction_pagination_filtering_sorting(client):
    headers = get_auth_headers(client, "query@example.com")

    # Create 3 transactions with different values & dates
    client.post(
        "/transactions/",
        headers=headers,
        json={"amount": 10.0, "type": "expense", "category": "Food", "date": "2026-05-01T10:00:00"}
    )
    client.post(
        "/transactions/",
        headers=headers,
        json={"amount": 50.0, "type": "expense", "category": "Transport", "date": "2026-05-10T10:00:00"}
    )
    client.post(
        "/transactions/",
        headers=headers,
        json={"amount": 500.0, "type": "income", "category": "Other", "date": "2026-05-15T10:00:00"}
    )

    # 1. Test filtering by type
    resp = client.get("/transactions/?type=expense", headers=headers)
    assert len(resp.json()) == 2

    # 2. Test filtering by category
    resp = client.get("/transactions/?category=Transport", headers=headers)
    assert len(resp.json()) == 1
    assert resp.json()[0]["amount"] == 50.0

    # 3. Test filtering by date range
    resp = client.get("/transactions/?start_date=2026-05-05T00:00:00&end_date=2026-05-12T00:00:00", headers=headers)
    assert len(resp.json()) == 1
    assert resp.json()[0]["category"] == "Transport"

    # 4. Test sorting by amount desc
    resp = client.get("/transactions/?sort_by=amount&order=desc", headers=headers)
    amounts = [t["amount"] for t in resp.json()]
    assert amounts == [500.0, 50.0, 10.0]

    # 5. Test pagination (limit 2, page 2 skips 2 items)
    resp = client.get("/transactions/?limit=2&page=2&sort_by=amount&order=desc", headers=headers)
    assert len(resp.json()) == 1
    assert resp.json()[0]["amount"] == 10.0

def test_update_transaction(client):
    headers = get_auth_headers(client, "update@example.com")
    create_resp = client.post(
        "/transactions/",
        headers=headers,
        json={"amount": 100, "type": "income", "category": "Other"}
    )
    tx_id = create_resp.json()["id"]

    patch_resp = client.patch(
        f"/transactions/{tx_id}",
        headers=headers,
        json={"amount": 250, "note": "Updated note", "category": "Food"}
    )
    assert patch_resp.status_code == 200
    data = patch_resp.json()
    assert data["amount"] == 250.0
    assert data["note"] == "Updated note"
    assert data["category"] == "Food"

def test_delete_transaction(client):
    headers = get_auth_headers(client, "delete@example.com")
    create_resp = client.post(
        "/transactions/",
        headers=headers,
        json={"amount": 100, "type": "income", "category": "Other"}
    )
    tx_id = create_resp.json()["id"]

    # Delete
    del_resp = client.delete(f"/transactions/{tx_id}", headers=headers)
    assert del_resp.status_code == 204

    # Verify deleted
    get_resp = client.get(f"/transactions/{tx_id}", headers=headers)
    assert get_resp.status_code == 404
