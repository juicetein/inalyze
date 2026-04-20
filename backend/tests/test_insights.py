from app.schemas.analytics import (
    AnalyticsSummary,
    BusinessPatternSummary,
    ChartAggregates,
    MetricValue,
    RankedMetricItem,
    RevenueConcentrationSummary,
    RevenueTrendSummary,
    StatusBreakdownItem,
)
from app.schemas.cleaning import CleanedDataset, CanonicalOrderRow, TransformationAuditSummary
from app.schemas.validation import DataQualitySummary
from app.services.insights.service import InsightService


def build_cleaned_dataset() -> CleanedDataset:
    return CleanedDataset(
        row_count=8,
        rows=[
            CanonicalOrderRow(row_number=1, customer_identifier="a@example.com", product_name="Cold Brew", order_total=60.0, order_date="2026-04-01", fulfillment_status="fulfilled", payment_status="paid"),
            CanonicalOrderRow(row_number=2, customer_identifier="b@example.com", product_name="Latte", order_total=20.0, order_date="2026-04-02", fulfillment_status="fulfilled", payment_status="paid"),
            CanonicalOrderRow(row_number=3, customer_identifier="a@example.com", product_name="Cold Brew", order_total=55.0, order_date="2026-04-03", fulfillment_status="fulfilled", payment_status="paid"),
            CanonicalOrderRow(row_number=4, customer_identifier="c@example.com", product_name="Cold Brew", order_total=15.0, order_date="2026-04-04", fulfillment_status="unknown", payment_status="paid"),
            CanonicalOrderRow(row_number=5, customer_identifier="d@example.com", product_name="Mocha", order_total=10.0, order_date="2026-04-08", fulfillment_status="fulfilled", payment_status="pending"),
            CanonicalOrderRow(row_number=6, customer_identifier="e@example.com", product_name="Latte", order_total=12.0, order_date="2026-04-09", fulfillment_status="fulfilled", payment_status="paid"),
            CanonicalOrderRow(row_number=7, customer_identifier="f@example.com", product_name="Latte", order_total=9.0, order_date="2026-04-10", fulfillment_status="fulfilled", payment_status="unknown"),
            CanonicalOrderRow(row_number=8, customer_identifier="g@example.com", product_name="Tea", order_total=8.0, order_date="2026-04-10", fulfillment_status="fulfilled", payment_status="paid"),
        ],
    )


def build_analytics(
    *,
    recent_direction: str = "down",
    recent_percent_change: float = -0.35,
    current_period_revenue: float = 39.0,
    previous_period_revenue: float = 60.0,
) -> AnalyticsSummary:
    return AnalyticsSummary(
        total_revenue=MetricValue(value=189.0, formatted_value="$189.00"),
        order_count=8,
        average_order_value=MetricValue(value=23.63, formatted_value="$23.63"),
        repeat_customer_count=1,
        repeat_customer_rate=0.1429,
        top_products_by_revenue=[
            RankedMetricItem(label="Cold Brew", revenue=130.0, order_count=3, revenue_share=0.6878),
            RankedMetricItem(label="Latte", revenue=41.0, order_count=3, revenue_share=0.2169),
        ],
        top_customers_by_revenue=[
            RankedMetricItem(label="a@example.com", revenue=115.0, order_count=2, revenue_share=0.6085),
            RankedMetricItem(label="b@example.com", revenue=20.0, order_count=1, revenue_share=0.1058),
        ],
        fulfillment_status_breakdown=[
            StatusBreakdownItem(status="fulfilled", count=7, share=0.875),
            StatusBreakdownItem(status="unknown", count=1, share=0.125),
        ],
        payment_status_breakdown=[
            StatusBreakdownItem(status="paid", count=6, share=0.75),
            StatusBreakdownItem(status="unknown", count=1, share=0.125),
            StatusBreakdownItem(status="pending", count=1, share=0.125),
        ],
        charts=ChartAggregates(),
        patterns=BusinessPatternSummary(
            revenue_trend=RevenueTrendSummary(
                direction="down",
                absolute_change=-52.0,
                percent_change=-0.47,
                current_period_revenue=8.0,
                previous_period_revenue=60.0,
                summary="",
            ),
            recent_sales_change=RevenueTrendSummary(
                direction=recent_direction,
                absolute_change=current_period_revenue - previous_period_revenue,
                percent_change=recent_percent_change,
                current_period_revenue=current_period_revenue,
                previous_period_revenue=previous_period_revenue,
                summary="",
            ),
            revenue_concentration=RevenueConcentrationSummary(
                top_product_share=0.6878,
                top_three_product_share=0.95,
                repeat_customer_revenue_share=0.6085,
                summary="",
            ),
        ),
    )


def test_top_product_win_insight() -> None:
    payload = InsightService().generate(
        cleaned_dataset=build_cleaned_dataset(),
        transformation_audit=TransformationAuditSummary(),
        data_quality=DataQualitySummary(),
        analytics=build_analytics(recent_direction="flat", recent_percent_change=0.0),
    )

    assert any(insight.title == "One product is clearly leading sales" for insight in payload.key_wins)


def test_missing_status_risk_insight() -> None:
    payload = InsightService().generate(
        cleaned_dataset=build_cleaned_dataset(),
        transformation_audit=TransformationAuditSummary(),
        data_quality=DataQualitySummary(),
        analytics=build_analytics(recent_direction="flat", recent_percent_change=0.0),
    )

    assert any(insight.title == "Some order statuses are missing or unclear" for insight in payload.risks_issues)


def test_revenue_decline_insight() -> None:
    payload = InsightService().generate(
        cleaned_dataset=build_cleaned_dataset(),
        transformation_audit=TransformationAuditSummary(),
        data_quality=DataQualitySummary(),
        analytics=build_analytics(),
    )

    assert any(insight.title == "Recent sales have declined" for insight in payload.risks_issues)


def test_follow_up_opportunity_insight() -> None:
    payload = InsightService().generate(
        cleaned_dataset=build_cleaned_dataset(),
        transformation_audit=TransformationAuditSummary(),
        data_quality=DataQualitySummary(),
        analytics=build_analytics(recent_direction="flat", recent_percent_change=0.0),
    )

    assert any(insight.title == "Follow up with strong one-time buyers" for insight in payload.recommended_actions)


def test_suppression_of_weak_insights_on_small_dataset() -> None:
    small_dataset = CleanedDataset(
        row_count=3,
        rows=[
            CanonicalOrderRow(row_number=1, customer_identifier="a@example.com", product_name="Cold Brew", order_total=60.0, order_date="2026-04-01", fulfillment_status="fulfilled", payment_status="paid"),
            CanonicalOrderRow(row_number=2, customer_identifier="b@example.com", product_name="Latte", order_total=20.0, order_date="2026-04-02", fulfillment_status="fulfilled", payment_status="paid"),
            CanonicalOrderRow(row_number=3, customer_identifier="c@example.com", product_name="Tea", order_total=18.0, order_date="2026-04-03", fulfillment_status="fulfilled", payment_status="paid"),
        ],
    )
    small_analytics = AnalyticsSummary(
        total_revenue=MetricValue(value=98.0, formatted_value="$98.00"),
        order_count=3,
        average_order_value=MetricValue(value=32.67, formatted_value="$32.67"),
        repeat_customer_count=0,
        repeat_customer_rate=0.0,
        top_products_by_revenue=[RankedMetricItem(label="Cold Brew", revenue=60.0, order_count=1, revenue_share=0.6122)],
        top_customers_by_revenue=[RankedMetricItem(label="a@example.com", revenue=60.0, order_count=1, revenue_share=0.6122)],
        fulfillment_status_breakdown=[StatusBreakdownItem(status="fulfilled", count=3, share=1.0)],
        payment_status_breakdown=[StatusBreakdownItem(status="paid", count=3, share=1.0)],
        charts=ChartAggregates(),
        patterns=BusinessPatternSummary(
            revenue_trend=RevenueTrendSummary(direction="up", absolute_change=10.0, percent_change=0.2, current_period_revenue=60.0, previous_period_revenue=50.0, summary=""),
            recent_sales_change=RevenueTrendSummary(direction="up", absolute_change=10.0, percent_change=0.2, current_period_revenue=60.0, previous_period_revenue=50.0, summary=""),
            revenue_concentration=RevenueConcentrationSummary(top_product_share=0.6122, top_three_product_share=1.0, repeat_customer_revenue_share=0.0, summary=""),
        ),
    )

    payload = InsightService().generate(
        cleaned_dataset=small_dataset,
        transformation_audit=TransformationAuditSummary(),
        data_quality=DataQualitySummary(),
        analytics=small_analytics,
    )

    assert payload.suppressed_due_to_small_dataset is True
    assert payload.key_wins == []
    assert not any(insight.title == "Follow up with strong one-time buyers" for insight in payload.recommended_actions)
