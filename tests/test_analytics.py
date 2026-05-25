from datetime import datetime
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

def test_analytics_summary_and_categories(client):
    headers = get_auth_headers(client, "analytics@example.com")

    # Add transactions
    # Income: 1000, 500 = 1500
    # Expense: 200 (Food), 300 (Transport) = 500
    # Balance = 1000
    client.post(
        "/transactions/",
        headers=headers,
        json={"amount": 1000.0, "type": "income", "category": "Other", "date": "2026-05-01T10:00:00"}
    )
    client.post(
        "/transactions/",
        headers=headers,
        json={"amount": 500.0, "type": "income", "category": "Other", "date": "2026-05-02T10:00:00"}
    )
    client.post(
        "/transactions/",
        headers=headers,
        json={"amount": 200.0, "type": "expense", "category": "Food", "date": "2026-05-03T10:00:00"}
    )
    client.post(
        "/transactions/",
        headers=headers,
        json={"amount": 300.0, "type": "expense", "category": "Transport", "date": "2026-05-04T10:00:00"}
    )

    # Verify Summary
    summary_resp = client.get("/analytics/summary", headers=headers)
    assert summary_resp.status_code == 200
    summary = summary_resp.json()
    assert summary["income"] == 1500.0
    assert summary["expenses"] == 500.0
    assert summary["balance"] == 1000.0

    # Verify Summary with date range
    summary_range_resp = client.get(
        "/analytics/summary?start_date=2026-05-02T00:00:00&end_date=2026-05-03T23:59:59",
        headers=headers
    )
    assert summary_range_resp.status_code == 200
    summary_range = summary_range_resp.json()
    assert summary_range["income"] == 500.0
    assert summary_range["expenses"] == 200.0
    assert summary_range["balance"] == 300.0

    # Verify Category Breakdown
    # Total expenses: 500
    # Food: 200 (40.0%), Transport: 300 (60.0%)
    categories_resp = client.get("/analytics/categories", headers=headers)
    assert categories_resp.status_code == 200
    categories = categories_resp.json()
    assert len(categories) == 2
    
    # Sorted by amount desc
    assert categories[0]["category"] == "Transport"
    assert categories[0]["amount"] == 300.0
    assert categories[0]["percentage"] == 60.0

    assert categories[1]["category"] == "Food"
    assert categories[1]["amount"] == 200.0
    assert categories[1]["percentage"] == 40.0

def test_analytics_monthly_trends(client):
    headers = get_auth_headers(client, "monthly_trends@example.com")
    
    # Add transactions in different months
    # 2026-04: income 800, expense 300
    # 2026-05: income 1500, expense 400
    client.post(
        "/transactions/",
        headers=headers,
        json={"amount": 800.0, "type": "income", "category": "Other", "date": "2026-04-15T12:00:00"}
    )
    client.post(
        "/transactions/",
        headers=headers,
        json={"amount": 300.0, "type": "expense", "category": "Food", "date": "2026-04-20T12:00:00"}
    )
    client.post(
        "/transactions/",
        headers=headers,
        json={"amount": 1500.0, "type": "income", "category": "Other", "date": "2026-05-01T12:00:00"}
    )
    client.post(
        "/transactions/",
        headers=headers,
        json={"amount": 400.0, "type": "expense", "category": "Transport", "date": "2026-05-05T12:00:00"}
    )

    resp = client.get("/analytics/monthly?months=3", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    
    # We expect to find records for 2026-04 and 2026-05
    months_data = {r["month"]: r for r in data}
    assert "2026-04" in months_data
    assert "2026-05" in months_data

    assert months_data["2026-04"]["income"] == 800.0
    assert months_data["2026-04"]["expense"] == 300.0

    assert months_data["2026-05"]["income"] == 1500.0
    assert months_data["2026-05"]["expense"] == 400.0
