def test_create_and_get_item(client):
    resp = client.post(
        "/items",
        json={"name": "Keyboard", "quantity": 10, "price": 2500.50, "category": "electronics"},
    )
    assert resp.status_code == 201
    created = resp.get_json()
    assert created["id"] > 0
    assert created["name"] == "Keyboard"
    assert created["quantity"] == 10
    assert created["category"] == "electronics"

    item_id = created["id"]
    resp2 = client.get(f"/items/{item_id}")
    assert resp2.status_code == 200
    got = resp2.get_json()
    assert got["id"] == item_id


def test_create_item_validation_quantity_not_negative(client):
    resp = client.post(
        "/items",
        json={"name": "Bad", "quantity": -1, "price": 10, "category": "test"},
    )
    assert resp.status_code == 400


def test_list_items_and_filter_by_category(client):
    client.post(
        "/items",
        json={"name": "A", "quantity": 1, "price": 10, "category": "cat1"},
    )
    client.post(
        "/items",
        json={"name": "B", "quantity": 2, "price": 20, "category": "cat2"},
    )

    resp = client.get("/items")
    assert resp.status_code == 200
    items = resp.get_json()
    assert len(items) == 2

    resp2 = client.get("/items?category=cat1")
    assert resp2.status_code == 200
    items2 = resp2.get_json()
    assert len(items2) == 1
    assert items2[0]["category"] == "cat1"


def test_update_item_and_delete_item(client):
    resp = client.post(
        "/items",
        json={"name": "Mouse", "quantity": 5, "price": 999.99, "category": "electronics"},
    )
    item_id = resp.get_json()["id"]

    resp2 = client.put(f"/items/{item_id}", json={"quantity": 0})
    assert resp2.status_code == 200
    updated = resp2.get_json()
    assert updated["quantity"] == 0

    resp3 = client.delete(f"/items/{item_id}")
    assert resp3.status_code == 204

    resp4 = client.get(f"/items/{item_id}")
    assert resp4.status_code == 404


def test_reports_summary_json_and_csv(client):
    client.post(
        "/items",
        json={"name": "Item1", "quantity": 10, "price": 100, "category": "electronics"},
    )
    client.post(
        "/items",
        json={"name": "Item2", "quantity": 2, "price": 50, "category": "office"},
    )
    client.post(
        "/items",
        json={"name": "Item3", "quantity": 0, "price": 200, "category": "electronics"},
    )

    resp = client.get("/reports/summary")
    assert resp.status_code == 200
    summary = resp.get_json()
    assert summary["total_value"] == 1100.0

    categories = {c["category"]: c for c in summary["categories"]}
    assert categories["electronics"]["items_count"] == 2
    assert categories["electronics"]["total_quantity"] == 10
    assert categories["electronics"]["total_value"] == 1000.0
    assert categories["office"]["items_count"] == 1
    assert categories["office"]["total_quantity"] == 2
    assert categories["office"]["total_value"] == 100.0

    non_positive = summary["items_with_non_positive_quantity"]
    assert any(i["name"] == "Item3" and i["quantity"] == 0 for i in non_positive)

    resp2 = client.get("/reports/summary?format=csv")
    assert resp2.status_code == 200
    assert resp2.mimetype == "text/csv"
    text = resp2.get_data(as_text=True)
    assert "category,items_count,total_quantity,total_value" in text

