import pytest

def get_auth_headers(client, email):
    client.post(
        "/auth/register",
        json={"name": "User", "email": email, "password": "password123"}
    )
    login_resp = client.post(
        "/auth/login",
        json={"email": email, "password": "password123"}
    )
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_list_categories(client):
    headers = get_auth_headers(client, "cat1@example.com")
    response = client.get("/categories/", headers=headers)
    assert response.status_code == 200
    names = [c["name"] for c in response.json()]
    for default_cat in ["Food", "Transport", "Bills", "Health", "Shopping", "Travel", "Leisure", "Other"]:
        assert default_cat in names

def test_create_custom_category(client):
    headers = get_auth_headers(client, "cat2@example.com")
    response = client.post(
        "/categories/",
        headers=headers,
        json={"name": "Gadgets"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Gadgets"
    assert data["is_default"] is False

    # Check that list includes the new custom category
    list_resp = client.get("/categories/", headers=headers)
    names = [c["name"] for c in list_resp.json()]
    assert "Gadgets" in names

def test_create_duplicate_category(client):
    headers = get_auth_headers(client, "cat3@example.com")
    # Duplicate of default
    resp1 = client.post("/categories/", headers=headers, json={"name": "Food"})
    assert resp1.status_code == 400

    # Duplicate of custom
    client.post("/categories/", headers=headers, json={"name": "Hobbies"})
    resp2 = client.post("/categories/", headers=headers, json={"name": "Hobbies"})
    assert resp2.status_code == 400

def test_update_category_restrictions(client):
    headers = get_auth_headers(client, "cat4@example.com")
    
    # 1. Fetch categories to get IDs
    list_resp = client.get("/categories/", headers=headers)
    categories = list_resp.json()
    default_cat = [c for c in categories if c["is_default"]][0]

    # 2. Try to update default category
    resp = client.patch(
        f"/categories/{default_cat['id']}",
        headers=headers,
        json={"name": "SuperFood"}
    )
    assert resp.status_code == 403
    assert "Default categories cannot be updated" in resp.json()["detail"]

    # 3. Create custom and update it
    custom_resp = client.post("/categories/", headers=headers, json={"name": "Gym"})
    custom_id = custom_resp.json()["id"]

    update_resp = client.patch(
        f"/categories/{custom_id}",
        headers=headers,
        json={"name": "Fitness"}
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["name"] == "Fitness"

def test_delete_category_restrictions(client):
    headers = get_auth_headers(client, "cat5@example.com")
    
    # 1. Fetch categories to get IDs
    list_resp = client.get("/categories/", headers=headers)
    categories = list_resp.json()
    default_cat = [c for c in categories if c["is_default"]][0]

    # 2. Try to delete default category
    resp = client.delete(f"/categories/{default_cat['id']}", headers=headers)
    assert resp.status_code == 403

    # 3. Create custom, add transaction using it, try to delete category
    custom_resp = client.post("/categories/", headers=headers, json={"name": "Books"})
    custom_id = custom_resp.json()["id"]

    client.post(
        "/transactions/",
        headers=headers,
        json={"amount": 45.0, "type": "expense", "category": "Books"}
    )

    # Deleting custom category in use should fail
    del_resp1 = client.delete(f"/categories/{custom_id}", headers=headers)
    assert del_resp1.status_code == 400
    assert "in use by transactions" in del_resp1.json()["detail"]

    # Create another custom not in use, delete it
    custom2_resp = client.post("/categories/", headers=headers, json={"name": "Music"})
    custom2_id = custom2_resp.json()["id"]
    del_resp2 = client.delete(f"/categories/{custom2_id}", headers=headers)
    assert del_resp2.status_code == 204
