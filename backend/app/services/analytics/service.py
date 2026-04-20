from collections import Counter, defaultdict
from datetime import date, timedelta

from app.schemas.analytics import (
    AnalyticsSummary,
    BusinessPatternSummary,
    CategorySeriesPoint,
    ChartAggregates,
    MetricValue,
    RankedMetricItem,
    RevenueConcentrationSummary,
    RevenueTrendSummary,
    StatusBreakdownItem,
    StatusSeriesPoint,
    TimeSeriesPoint,
)
from app.schemas.cleaning import CanonicalOrderRow, CleanedDataset


class AnalyticsService:
    def analyze(self, cleaned_dataset: CleanedDataset) -> AnalyticsSummary:
        rows = cleaned_dataset.rows
        total_revenue = self._sum_revenue(rows)
        order_count = len(rows)
        average_order_value = total_revenue / order_count if order_count else 0.0

        customer_counts = self._customer_order_counts(rows)
        repeat_customer_ids = {customer for customer, count in customer_counts.items() if count > 1}
        repeat_customer_count = len(repeat_customer_ids)
        repeat_customer_rate = repeat_customer_count / len(customer_counts) if customer_counts else 0.0

        top_products = self._rank_entities(
            rows=rows,
            key_getter=lambda row: row.product_name or "Unknown Product",
            limit=5,
            total_revenue=total_revenue,
        )
        top_customers = self._rank_entities(
            rows=rows,
            key_getter=lambda row: row.customer_identifier or "Unknown Customer",
            limit=5,
            total_revenue=total_revenue,
        )

        fulfillment_breakdown = self._status_breakdown(
            values=[row.fulfillment_status for row in rows],
            total_count=order_count,
        )
        payment_breakdown = self._status_breakdown(
            values=[row.payment_status for row in rows],
            total_count=order_count,
        )

        sales_over_time = self._sales_over_time(rows)
        revenue_by_product = self._category_series(top_products)
        top_customers_series = self._category_series(top_customers)
        status_chart = self._status_chart(fulfillment_breakdown, payment_breakdown)

        revenue_trend = self._revenue_trend(sales_over_time)
        recent_sales_change = self._recent_sales_change(sales_over_time)
        revenue_concentration = self._revenue_concentration(
            total_revenue=total_revenue,
            top_products=top_products,
            rows=rows,
            repeat_customer_ids=repeat_customer_ids,
        )

        return AnalyticsSummary(
            total_revenue=MetricValue(
                value=round(total_revenue, 2),
                formatted_value=self._format_currency(total_revenue),
            ),
            order_count=order_count,
            average_order_value=MetricValue(
                value=round(average_order_value, 2),
                formatted_value=self._format_currency(average_order_value),
            ),
            repeat_customer_count=repeat_customer_count,
            repeat_customer_rate=round(repeat_customer_rate, 4),
            top_products_by_revenue=top_products,
            top_customers_by_revenue=top_customers,
            fulfillment_status_breakdown=fulfillment_breakdown,
            payment_status_breakdown=payment_breakdown,
            charts=ChartAggregates(
                sales_over_time=sales_over_time,
                revenue_by_product=revenue_by_product,
                top_customers=top_customers_series,
                status_breakdown=status_chart,
            ),
            patterns=BusinessPatternSummary(
                revenue_trend=revenue_trend,
                recent_sales_change=recent_sales_change,
                revenue_concentration=revenue_concentration,
            ),
        )

    @staticmethod
    def _sum_revenue(rows: list[CanonicalOrderRow]) -> float:
        return sum(row.order_total or 0.0 for row in rows)

    @staticmethod
    def _customer_order_counts(rows: list[CanonicalOrderRow]) -> dict[str, int]:
        counts: Counter[str] = Counter()
        for row in rows:
            if row.customer_identifier:
                counts[row.customer_identifier] += 1
        return dict(counts)

    def _rank_entities(
        self,
        rows: list[CanonicalOrderRow],
        key_getter,
        limit: int,
        total_revenue: float,
    ) -> list[RankedMetricItem]:
        grouped_revenue: dict[str, float] = defaultdict(float)
        grouped_orders: dict[str, int] = defaultdict(int)

        for row in rows:
            key = key_getter(row)
            grouped_revenue[key] += row.order_total or 0.0
            grouped_orders[key] += 1

        ranked = sorted(
            grouped_revenue.items(),
            key=lambda item: (-item[1], item[0]),
        )[:limit]

        return [
            RankedMetricItem(
                label=label,
                revenue=round(revenue, 2),
                order_count=grouped_orders[label],
                revenue_share=round((revenue / total_revenue) if total_revenue else 0.0, 4),
            )
            for label, revenue in ranked
        ]

    @staticmethod
    def _status_breakdown(values: list[str], total_count: int) -> list[StatusBreakdownItem]:
        counts = Counter(values)
        return [
            StatusBreakdownItem(
                status=status,
                count=count,
                share=round((count / total_count) if total_count else 0.0, 4),
            )
            for status, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
        ]

    @staticmethod
    def _sales_over_time(rows: list[CanonicalOrderRow]) -> list[TimeSeriesPoint]:
        grouped_revenue: dict[str, float] = defaultdict(float)
        grouped_orders: dict[str, int] = defaultdict(int)

        for row in rows:
            if not row.order_date:
                continue
            grouped_revenue[row.order_date] += row.order_total or 0.0
            grouped_orders[row.order_date] += 1

        return [
            TimeSeriesPoint(
                date=order_date,
                revenue=round(grouped_revenue[order_date], 2),
                order_count=grouped_orders[order_date],
            )
            for order_date in sorted(grouped_revenue)
        ]

    @staticmethod
    def _category_series(items: list[RankedMetricItem]) -> list[CategorySeriesPoint]:
        return [
            CategorySeriesPoint(
                label=item.label,
                revenue=item.revenue,
                order_count=item.order_count,
            )
            for item in items
        ]

    @staticmethod
    def _status_chart(
        fulfillment_breakdown: list[StatusBreakdownItem],
        payment_breakdown: list[StatusBreakdownItem],
    ) -> list[StatusSeriesPoint]:
        points: list[StatusSeriesPoint] = []
        for item in fulfillment_breakdown:
            points.append(
                StatusSeriesPoint(
                    status_type="fulfillment",
                    status=item.status,
                    count=item.count,
                )
            )
        for item in payment_breakdown:
            points.append(
                StatusSeriesPoint(
                    status_type="payment",
                    status=item.status,
                    count=item.count,
                )
            )
        return points

    def _revenue_trend(self, sales_over_time: list[TimeSeriesPoint]) -> RevenueTrendSummary:
        if len(sales_over_time) < 2:
            return RevenueTrendSummary(
                direction="insufficient_data",
                summary="There is not enough dated order history yet to measure a revenue trend.",
            )

        first = sales_over_time[0].revenue
        last = sales_over_time[-1].revenue
        change = last - first
        percent_change = (change / first) if first else 0.0
        direction = "flat"
        if change > 0:
            direction = "up"
        elif change < 0:
            direction = "down"

        return RevenueTrendSummary(
            direction=direction,
            absolute_change=round(change, 2),
            percent_change=round(percent_change, 4),
            current_period_revenue=round(last, 2),
            previous_period_revenue=round(first, 2),
            summary=(
                f"Revenue moved from {self._format_currency(first)} to "
                f"{self._format_currency(last)} across the dated order history."
            ),
        )

    def _recent_sales_change(self, sales_over_time: list[TimeSeriesPoint]) -> RevenueTrendSummary:
        if len(sales_over_time) < 2:
            return RevenueTrendSummary(
                direction="insufficient_data",
                summary="There is not enough dated order history yet to compare recent sales periods.",
            )

        latest_date = date.fromisoformat(sales_over_time[-1].date)
        current_start = latest_date - timedelta(days=6)
        previous_end = current_start - timedelta(days=1)
        previous_start = previous_end - timedelta(days=6)

        current_revenue = sum(
            point.revenue
            for point in sales_over_time
            if current_start <= date.fromisoformat(point.date) <= latest_date
        )
        previous_revenue = sum(
            point.revenue
            for point in sales_over_time
            if previous_start <= date.fromisoformat(point.date) <= previous_end
        )

        if current_revenue == 0 and previous_revenue == 0:
            return RevenueTrendSummary(
                direction="insufficient_data",
                summary="There is not enough recent activity to compare the last two weekly periods.",
            )

        change = current_revenue - previous_revenue
        percent_change = (change / previous_revenue) if previous_revenue else 0.0
        direction = "flat"
        if change > 0:
            direction = "up"
        elif change < 0:
            direction = "down"

        return RevenueTrendSummary(
            direction=direction,
            absolute_change=round(change, 2),
            percent_change=round(percent_change, 4),
            current_period_revenue=round(current_revenue, 2),
            previous_period_revenue=round(previous_revenue, 2),
            summary=(
                f"Recent sales were {self._format_currency(current_revenue)} in the latest 7-day window "
                f"versus {self._format_currency(previous_revenue)} in the prior 7-day window."
            ),
        )

    def _revenue_concentration(
        self,
        total_revenue: float,
        top_products: list[RankedMetricItem],
        rows: list[CanonicalOrderRow],
        repeat_customer_ids: set[str],
    ) -> RevenueConcentrationSummary:
        top_product_share = top_products[0].revenue_share if top_products else 0.0
        top_three_product_share = round(sum(item.revenue_share for item in top_products[:3]), 4)
        repeat_customer_revenue = sum(
            row.order_total or 0.0
            for row in rows
            if row.customer_identifier and row.customer_identifier in repeat_customer_ids
        )
        repeat_customer_revenue_share = round(
            (repeat_customer_revenue / total_revenue) if total_revenue else 0.0,
            4,
        )

        return RevenueConcentrationSummary(
            top_product_share=round(top_product_share, 4),
            top_three_product_share=top_three_product_share,
            repeat_customer_revenue_share=repeat_customer_revenue_share,
            summary=(
                f"The top product accounts for {top_product_share:.1%} of revenue, "
                f"the top three products account for {top_three_product_share:.1%}, "
                f"and repeat customers account for {repeat_customer_revenue_share:.1%}."
            ),
        )

    @staticmethod
    def _format_currency(value: float) -> str:
        return f"${value:,.2f}"
