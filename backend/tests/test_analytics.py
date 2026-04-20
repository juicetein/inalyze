from app.schemas.cleaning import CanonicalOrderRow, CleanedDataset
from app.services.analytics.service import AnalyticsService


def build_dataset() -> CleanedDataset:
    return CleanedDataset(
        row_count=6,
        rows=[
            CanonicalOrderRow(
                row_number=1,
                order_id="1",
                customer_identifier="alice@example.com",
                product_name="Cold Brew",
                order_total=30.0,
                order_date="2026-04-01",
                fulfillment_status="fulfilled",
                payment_status="paid",
            ),
            CanonicalOrderRow(
                row_number=2,
                order_id="2",
                customer_identifier="bob@example.com",
                product_name="Latte",
                order_total=20.0,
                order_date="2026-04-02",
                fulfillment_status="pending",
                payment_status="pending",
            ),
            CanonicalOrderRow(
                row_number=3,
                order_id="3",
                customer_identifier="alice@example.com",
                product_name="Cold Brew",
                order_total=40.0,
                order_date="2026-04-03",
                fulfillment_status="fulfilled",
                payment_status="paid",
            ),
            CanonicalOrderRow(
                row_number=4,
                order_id="4",
                customer_identifier="carol@example.com",
                product_name="Mocha",
                order_total=10.0,
                order_date="2026-04-08",
                fulfillment_status="cancelled",
                payment_status="failed",
            ),
            CanonicalOrderRow(
                row_number=5,
                order_id="5",
                customer_identifier="bob@example.com",
                product_name="Latte",
                order_total=50.0,
                order_date="2026-04-09",
                fulfillment_status="fulfilled",
                payment_status="paid",
            ),
            CanonicalOrderRow(
                row_number=6,
                order_id="6",
                customer_identifier="dave@example.com",
                product_name="Latte",
                order_total=25.0,
                order_date="2026-04-10",
                fulfillment_status="fulfilled",
                payment_status="paid",
            ),
        ],
    )


def test_core_metric_calculation() -> None:
    analytics = AnalyticsService().analyze(build_dataset())

    assert analytics.total_revenue.value == 175.0
    assert analytics.order_count == 6
    assert analytics.average_order_value.value == round(175.0 / 6, 2)


def test_repeat_customer_calculation() -> None:
    analytics = AnalyticsService().analyze(build_dataset())

    assert analytics.repeat_customer_count == 2
    assert analytics.repeat_customer_rate == 0.5


def test_top_product_aggregation() -> None:
    analytics = AnalyticsService().analyze(build_dataset())

    top_product = analytics.top_products_by_revenue[0]
    assert top_product.label == "Latte"
    assert top_product.revenue == 95.0
    assert top_product.order_count == 3


def test_revenue_over_time_aggregation() -> None:
    analytics = AnalyticsService().analyze(build_dataset())

    assert analytics.charts.sales_over_time[0].date == "2026-04-01"
    assert analytics.charts.sales_over_time[0].revenue == 30.0
    assert analytics.charts.sales_over_time[-1].date == "2026-04-10"
    assert analytics.charts.sales_over_time[-1].revenue == 25.0


def test_status_breakdown_aggregation() -> None:
    analytics = AnalyticsService().analyze(build_dataset())

    fulfillment = {item.status: item.count for item in analytics.fulfillment_status_breakdown}
    payment = {item.status: item.count for item in analytics.payment_status_breakdown}

    assert fulfillment["fulfilled"] == 4
    assert fulfillment["pending"] == 1
    assert fulfillment["cancelled"] == 1
    assert payment["paid"] == 4
    assert payment["pending"] == 1
    assert payment["failed"] == 1
