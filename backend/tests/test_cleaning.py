from app.schemas.validation import ColumnInferenceResult
from app.services.cleaning.normalizers import (
    DateNormalizer,
    NumericNormalizer,
    ProductNormalizer,
    StatusNormalizer,
)
from app.services.cleaning.service import CleaningService


def test_product_name_normalization() -> None:
    normalized = ProductNormalizer().normalize("  cold-brew_concentrate  ")
    assert normalized == "Cold Brew Concentrate"


def test_numeric_cleaning() -> None:
    normalized = NumericNormalizer().normalize("($1,240.50)")
    assert normalized == -1240.50


def test_date_normalization() -> None:
    normalized = DateNormalizer().normalize("04/20/2026 3:45 PM")
    assert normalized == "2026-04-20"


def test_status_normalization() -> None:
    normalizer = StatusNormalizer()
    assert normalizer.normalize_fulfillment("Shipped") == "fulfilled"
    assert normalizer.normalize_payment("Awaiting Payment") == "pending"


def test_transformation_logging() -> None:
    inferred_columns = [
        ColumnInferenceResult(role="order_id", column_name="Order ID", confidence="high", reason=""),
        ColumnInferenceResult(role="customer", column_name="Customer", confidence="high", reason=""),
        ColumnInferenceResult(role="product", column_name="Product", confidence="high", reason=""),
        ColumnInferenceResult(role="quantity", column_name="Qty", confidence="high", reason=""),
        ColumnInferenceResult(role="price", column_name="Total", confidence="high", reason=""),
        ColumnInferenceResult(role="date", column_name="Date", confidence="high", reason=""),
        ColumnInferenceResult(
            role="fulfillment_status",
            column_name="Fulfillment",
            confidence="high",
            reason="",
        ),
        ColumnInferenceResult(
            role="payment_status",
            column_name="Payment",
            confidence="high",
            reason="",
        ),
    ]
    rows = [
        {
            "Order ID": " 1001 ",
            "Customer": "customer@example.com",
            "Product": " cold-brew_concentrate ",
            "Qty": "2",
            "Total": "$24.50",
            "Date": "04/20/2026 3:45 PM",
            "Fulfillment": "Shipped",
            "Payment": "",
        }
    ]

    dataset, audit = CleaningService().clean(rows=rows, inferred_columns=inferred_columns)

    assert dataset.rows[0].order_id == "1001"
    assert dataset.rows[0].product_name == "Cold Brew Concentrate"
    assert dataset.rows[0].order_total == 24.50
    assert dataset.rows[0].order_date == "2026-04-20"
    assert dataset.rows[0].payment_status == "unknown"
    assert audit.total_changes >= 4
    assert audit.field_change_counts["product_name"] >= 1
    assert any(entry.field == "payment_status" for entry in audit.entries)
