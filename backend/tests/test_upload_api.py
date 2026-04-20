from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_invalid_file_type_is_rejected() -> None:
    response = client.post(
        "/api/v1/uploads/csv",
        files={"file": ("orders.txt", b"not,csv", "text/plain")},
    )

    assert response.status_code == 415
    assert response.json()["detail"]["code"] == "invalid_extension"


def test_malformed_csv_is_tolerated_and_reported() -> None:
    csv_content = (
        "Order ID,Product,Price,Date\n"
        "1001,Cold Brew,24.00,2026-04-01\n"
        "1002,Latte,18.50\n"
        "1003,Mocha,15.00,2026-04-03,EXTRA\n"
    )

    response = client.post(
        "/api/v1/uploads/csv",
        files={"file": ("orders.csv", csv_content.encode("utf-8"), "text/csv")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["parsing_summary"]["malformed_row_count"] == 2
    assert any(
        issue["code"] == "malformed_rows"
        for issue in body["data_quality"]["issues"]
    )
