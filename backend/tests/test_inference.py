from app.services.ingestion.inference import ColumnInferenceService


def test_infers_core_columns_from_common_headers() -> None:
    headers = [
        "Order ID",
        "Customer Email",
        "Product Name",
        "Qty",
        "Order Total",
        "Created At",
        "Fulfillment Status",
        "Financial Status",
    ]
    rows = [
        {
            "Order ID": "1001",
            "Customer Email": "owner@example.com",
            "Product Name": "Cold Brew",
            "Qty": "2",
            "Order Total": "$24.00",
            "Created At": "2026-04-01",
            "Fulfillment Status": "fulfilled",
            "Financial Status": "paid",
        }
    ]

    results = ColumnInferenceService().infer(headers, rows)
    role_map = {result.role: result.column_name for result in results}

    assert role_map["order_id"] == "Order ID"
    assert role_map["customer"] == "Customer Email"
    assert role_map["product"] == "Product Name"
    assert role_map["quantity"] == "Qty"
    assert role_map["price"] == "Order Total"
    assert role_map["date"] == "Created At"
