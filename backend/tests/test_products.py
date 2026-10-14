import pytest


def make_product(client, **overrides):
    payload = {
        "sku": "KB-001",
        "name": "Mechanical Keyboard",
        "description": "87-key, brown switches",
        "category": "Peripherals",
        "supplier": "KeyCo",
        "quantity": 25,
        "reorder_level": 5,
        "unit_price": 49.99,
    }
    payload.update(overrides)
    response = client.post("/api/products", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def test_health_returns_up(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "UP"}


def test_ready_checks_database(client):
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "READY"


def test_metrics_exposes_prometheus_format(client):
    client.get("/health")
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "http_requests_total" in response.text


def test_create_product(client):
    product = make_product(client)
    assert product["id"] > 0
    assert product["sku"] == "KB-001"
    assert product["unit_price"] == 49.99
    assert product["low_stock"] is False


def test_create_product_rejects_duplicate_sku(client):
    make_product(client)
    response = client.post("/api/products", json={"sku": "KB-001", "name": "Another"})
    assert response.status_code == 409


@pytest.mark.parametrize(
    "payload",
    [
        {"sku": "X-1", "name": ""},
        {"sku": "X-1", "name": "Cable", "quantity": -1},
        {"sku": "X-1", "name": "Cable", "unit_price": -5},
        {"name": "Missing SKU"},
    ],
)
def test_create_product_validates_input(client, payload):
    assert client.post("/api/products", json=payload).status_code == 422


def test_list_products_newest_first_and_filter_by_category(client):
    make_product(client, sku="A-1", name="Mouse", category="Peripherals")
    make_product(client, sku="B-1", name="USB-C Cable", category="Cables")

    all_products = client.get("/api/products").json()
    assert [p["sku"] for p in all_products] == ["B-1", "A-1"]

    cables = client.get("/api/products", params={"category": "Cables"}).json()
    assert [p["sku"] for p in cables] == ["B-1"]


def test_get_product_by_id(client):
    created = make_product(client)
    response = client.get(f"/api/products/{created['id']}")
    assert response.status_code == 200
    assert response.json()["name"] == "Mechanical Keyboard"


def test_get_missing_product_returns_404(client):
    response = client.get("/api/products/9999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Product not found"


def test_update_product_partial(client):
    created = make_product(client)
    response = client.put(
        f"/api/products/{created['id']}", json={"quantity": 3, "unit_price": 45.0}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["quantity"] == 3
    assert body["unit_price"] == 45.0
    assert body["low_stock"] is True
    assert body["name"] == "Mechanical Keyboard"


def test_update_missing_product_returns_404(client):
    assert client.put("/api/products/9999", json={"quantity": 1}).status_code == 404


def test_delete_product(client):
    created = make_product(client)
    assert client.delete(f"/api/products/{created['id']}").status_code == 204
    assert client.get(f"/api/products/{created['id']}").status_code == 404


def test_adjust_stock_receive_and_ship(client):
    created = make_product(client, quantity=10)
    received = client.post(f"/api/products/{created['id']}/adjust", json={"delta": 15})
    assert received.json()["quantity"] == 25

    shipped = client.post(f"/api/products/{created['id']}/adjust", json={"delta": -20})
    assert shipped.json()["quantity"] == 5


def test_adjust_stock_cannot_go_negative(client):
    created = make_product(client, quantity=2)
    response = client.post(f"/api/products/{created['id']}/adjust", json={"delta": -3})
    assert response.status_code == 400
    assert client.get(f"/api/products/{created['id']}").json()["quantity"] == 2


def test_adjust_stock_rejects_zero_delta(client):
    created = make_product(client)
    response = client.post(f"/api/products/{created['id']}/adjust", json={"delta": 0})
    assert response.status_code == 422


def test_stats_summarise_inventory(client):
    make_product(client, sku="A", quantity=10, reorder_level=5, unit_price=2.5)
    make_product(client, sku="B", quantity=3, reorder_level=5, unit_price=10)
    make_product(client, sku="C", quantity=0, reorder_level=5, unit_price=99)

    stats = client.get("/api/products/stats").json()
    assert stats == {
        "totalProducts": 3,
        "totalUnits": 13,
        "lowStock": 2,
        "outOfStock": 1,
        "inventoryValue": 55.0,
    }
