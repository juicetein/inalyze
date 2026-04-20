from app.schemas.validation import ColumnInferenceResult
from app.services.ingestion.validation import DatasetValidationService


def test_missing_required_fields_are_reported() -> None:
    inferred = [
        ColumnInferenceResult(
            role="order_id",
            column_name="Order ID",
            confidence="high",
            reason="Matched header alias.",
        ),
        ColumnInferenceResult(
            role="product",
            column_name="Product Name",
            confidence="high",
            reason="Matched header alias.",
        ),
    ]

    summary, messages = DatasetValidationService().summarize(
        rows=[{"Order ID": "1", "Product Name": "Latte"}],
        inferred_columns=inferred,
        malformed_row_count=0,
    )

    assert "price" in summary.missing_required_fields
    assert "date" in summary.missing_required_fields
    assert any(message.level == "error" for message in messages)
