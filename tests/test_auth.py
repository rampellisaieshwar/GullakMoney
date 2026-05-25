import pytest

def test_register_success(client):
    response = client.post(
        "/auth/register",
        json={"name": "Alice", "email": "alice@example.com", "password": "password123"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Alice"
    assert data["email"] == "alice@example.com"
    assert "id" in data

def test_register_duplicate_email(client):
    # Register once
    client.post(
        "/auth/register",
        json={"name": "Alice", "email": "alice@example.com", "password": "password123"}
    )
    # Register twice
    response = client.post(
        "/auth/register",
        json={"name": "Alice Duplicate", "email": "alice@example.com", "password": "password456"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"

def test_login_success(client):
    # Register
    client.post(
        "/auth/register",
        json={"name": "Bob", "email": "bob@example.com", "password": "password123"}
    )
    # Login
    response = client.post(
        "/auth/login",
        json={"email": "bob@example.com", "password": "password123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_invalid_password(client):
    # Register
    client.post(
        "/auth/register",
        json={"name": "Bob", "email": "bob@example.com", "password": "password123"}
    )
    # Login wrong pass
    response = client.post(
        "/auth/login",
        json={"email": "bob@example.com", "password": "wrongpassword"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"

def test_get_and_update_profile(client):
    # Register & Login
    client.post(
        "/auth/register",
        json={"name": "Charlie", "email": "charlie@example.com", "password": "password123"}
    )
    login_resp = client.post(
        "/auth/login",
        json={"email": "charlie@example.com", "password": "password123"}
    )
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Fetch profile
    profile_resp = client.get("/users/me", headers=headers)
    assert profile_resp.status_code == 200
    assert profile_resp.json()["name"] == "Charlie"

    # Update profile
    update_resp = client.put(
        "/users/me",
        headers=headers,
        json={"name": "Charlie Updated", "email": "charlie2@example.com"}
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["name"] == "Charlie Updated"
    assert update_resp.json()["email"] == "charlie2@example.com"

def test_change_password(client):
    # Register & Login
    client.post(
        "/auth/register",
        json={"name": "David", "email": "david@example.com", "password": "password123"}
    )
    login_resp = client.post(
        "/auth/login",
        json={"email": "david@example.com", "password": "password123"}
    )
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Change password
    change_resp = client.post(
        "/users/me/change-password",
        headers=headers,
        json={"current_password": "password123", "new_password": "newpassword123"}
    )
    assert change_resp.status_code == 200

    # Try login with old password
    old_login = client.post(
        "/auth/login",
        json={"email": "david@example.com", "password": "password123"}
    )
    assert old_login.status_code == 401

    # Login with new password
    new_login = client.post(
        "/auth/login",
        json={"email": "david@example.com", "password": "newpassword123"}
    )
    assert new_login.status_code == 200
