from collections import defaultdict

from app.schemas.analytics import AnalyticsSummary, RankedMetricItem, RevenueTrendSummary, StatusBreakdownItem
from app.schemas.cleaning import CleanedDataset, TransformationAuditSummary
from app.schemas.insights import InsightItem, InsightPayload
from app.schemas.validation import DataQualitySummary


class InsightService:
    SMALL_DATASET_ORDER_THRESHOLD = 5
    MIN_ORDER_THRESHOLD_FOR_TRENDS = 6
    TOP_PRODUCT_WIN_SHARE_THRESHOLD = 0.25
    REPEAT_CUSTOMER_RATE_THRESHOLD = 0.2
    POSITIVE_TREND_THRESHOLD = 0.15
    REVENUE_DECLINE_THRESHOLD = -0.15
    CUSTOMER_CONCENTRATION_RISK_THRESHOLD = 0.45
    STRONG_ONE_TIME_BUYER_MIN_SPEND = 50.0
    STATUS_RISK_THRESHOLD = 0.1

    def generate(
        self,
        cleaned_dataset: CleanedDataset,
        transformation_audit: TransformationAuditSummary,
        data_quality: DataQualitySummary,
        analytics: AnalyticsSummary,
    ) -> InsightPayload:
        small_dataset = analytics.order_count < self.SMALL_DATASET_ORDER_THRESHOLD
        wins: list[InsightItem] = []
        risks: list[InsightItem] = []
        actions: list[InsightItem] = []

        if not small_dataset:
            win = self._top_product_win(analytics)
            if win:
                wins.append(win)
                actions.append(self._restock_top_product_action(analytics))

            win = self._repeat_customer_win(analytics)
            if win:
                wins.append(win)

            win = self._positive_sales_trend_win(analytics)
            if win:
                wins.append(win)

            action = self._follow_up_one_time_buyers_action(cleaned_dataset)
            if action:
                actions.append(action)

        risk = self._missing_status_risk(analytics)
        if risk:
            risks.append(risk)

        risk = self._data_reliability_risk(data_quality, transformation_audit)
        if risk:
            risks.append(risk)
            actions.append(self._review_flagged_orders_action(data_quality, transformation_audit))

        risk = self._revenue_decline_risk(analytics)
        if risk:
            risks.append(risk)

        risk = self._customer_concentration_risk(analytics)
        if risk:
            risks.append(risk)

        wins = self._rank_and_trim(wins, limit=3)
        risks = self._rank_and_trim(risks, limit=4)
        actions = self._rank_and_trim(self._dedupe_actions(actions), limit=4)

        return InsightPayload(
            key_wins=wins,
            risks_issues=risks,
            recommended_actions=actions,
            suppressed_due_to_small_dataset=small_dataset,
            total_generated=len(wins) + len(risks) + len(actions),
        )

    def _top_product_win(self, analytics: AnalyticsSummary) -> InsightItem | None:
        if not analytics.top_products_by_revenue:
            return None

        top_product = analytics.top_products_by_revenue[0]
        if top_product.revenue_share < self.TOP_PRODUCT_WIN_SHARE_THRESHOLD:
            return None

        share_percent = round(top_product.revenue_share * 100, 1)
        return InsightItem(
            category="key_win",
            title="One product is clearly leading sales",
            statement=(
                f"{top_product.label} generated ${top_product.revenue:,.2f} in revenue, "
                f"which is {share_percent}% of total sales across {top_product.order_count} orders."
            ),
            why_it_matters=(
                "A product that already drives a large share of revenue is a strong lever for near-term growth."
            ),
            recommended_action=(
                f"Keep {top_product.label} in stock and feature it in your next promotion."
            ),
            supporting_data={
                "product_name": top_product.label,
                "product_revenue": top_product.revenue,
                "product_revenue_share": top_product.revenue_share,
                "product_order_count": top_product.order_count,
            },
            confidence="high",
            severity="info",
            evidence_label=f"{share_percent}% of revenue came from {top_product.label}",
            rank_score=80 + min(top_product.revenue_share * 100, 20),
        )

    def _repeat_customer_win(self, analytics: AnalyticsSummary) -> InsightItem | None:
        if analytics.repeat_customer_count <= 0:
            return None
        if analytics.repeat_customer_rate < self.REPEAT_CUSTOMER_RATE_THRESHOLD:
            return None

        share_percent = round(analytics.patterns.revenue_concentration.repeat_customer_revenue_share * 100, 1)
        rate_percent = round(analytics.repeat_customer_rate * 100, 1)
        return InsightItem(
            category="key_win",
            title="Repeat customers are already contributing meaningful revenue",
            statement=(
                f"{analytics.repeat_customer_count} repeat customers account for {rate_percent}% of your customer base "
                f"and {share_percent}% of revenue."
            ),
            why_it_matters=(
                "Returning buyers usually cost less to convert and can grow lifetime value faster than new customer acquisition."
            ),
            recommended_action=(
                "Create a simple loyalty follow-up or thank-you offer for your repeat customers."
            ),
            supporting_data={
                "repeat_customer_count": analytics.repeat_customer_count,
                "repeat_customer_rate": analytics.repeat_customer_rate,
                "repeat_customer_revenue_share": analytics.patterns.revenue_concentration.repeat_customer_revenue_share,
            },
            confidence="high",
            severity="info",
            evidence_label=f"Repeat customers drove {share_percent}% of revenue",
            rank_score=75 + min(rate_percent / 5, 15),
        )

    def _positive_sales_trend_win(self, analytics: AnalyticsSummary) -> InsightItem | None:
        trend = analytics.patterns.recent_sales_change
        if analytics.order_count < self.MIN_ORDER_THRESHOLD_FOR_TRENDS:
            return None
        if trend.direction != "up" or trend.percent_change < self.POSITIVE_TREND_THRESHOLD:
            return None

        change_percent = round(trend.percent_change * 100, 1)
        return InsightItem(
            category="key_win",
            title="Recent sales are trending upward",
            statement=(
                f"Revenue increased by {change_percent}% in the latest 7-day window, "
                f"rising from ${trend.previous_period_revenue:,.2f} to ${trend.current_period_revenue:,.2f}."
            ),
            why_it_matters=(
                "A recent sales lift can point to growing demand or a product mix that is working especially well."
            ),
            recommended_action=(
                "Review what changed in the last week and repeat the offer, product focus, or channel that drove the increase."
            ),
            supporting_data={
                "previous_period_revenue": trend.previous_period_revenue,
                "current_period_revenue": trend.current_period_revenue,
                "percent_change": trend.percent_change,
            },
            confidence="medium",
            severity="info",
            evidence_label=f"{change_percent}% recent revenue growth",
            rank_score=70 + min(change_percent / 5, 15),
        )

    def _missing_status_risk(self, analytics: AnalyticsSummary) -> InsightItem | None:
        status_issues: list[tuple[str, StatusBreakdownItem]] = []
        unknown_fulfillment = self._find_status(analytics.fulfillment_status_breakdown, "unknown")
        unknown_payment = self._find_status(analytics.payment_status_breakdown, "unknown")

        if unknown_fulfillment and unknown_fulfillment.share >= self.STATUS_RISK_THRESHOLD:
            status_issues.append(("fulfillment", unknown_fulfillment))
        if unknown_payment and unknown_payment.share >= self.STATUS_RISK_THRESHOLD:
            status_issues.append(("payment", unknown_payment))

        if not status_issues:
            return None

        parts = [
            f"{item.count} {status_type} status values ({round(item.share * 100, 1)}%) are unknown"
            for status_type, item in status_issues
        ]
        affected_count = sum(item.count for _, item in status_issues)
        return InsightItem(
            category="risk_issue",
            title="Some order statuses are missing or unclear",
            statement=f"{'; '.join(parts)}.",
            why_it_matters=(
                "Missing payment or fulfillment status can hide order problems and make the rest of the report less reliable."
            ),
            recommended_action=(
                "Review the affected orders and update missing status fields in the source system before acting on operational trends."
            ),
            supporting_data={
                "unknown_fulfillment_count": unknown_fulfillment.count if unknown_fulfillment else 0,
                "unknown_payment_count": unknown_payment.count if unknown_payment else 0,
            },
            confidence="high",
            severity="warning",
            evidence_label=f"{affected_count} orders have unknown status fields",
            rank_score=88 + affected_count,
        )

    def _data_reliability_risk(
        self,
        data_quality: DataQualitySummary,
        transformation_audit: TransformationAuditSummary,
    ) -> InsightItem | None:
        affected = (
            data_quality.duplicate_row_count
            + data_quality.invalid_numeric_value_count
            + data_quality.invalid_date_count
            + data_quality.suspicious_row_count
            + transformation_audit.flagged_row_count
        )
        if affected <= 0 and not data_quality.missing_required_fields:
            return None

        return InsightItem(
            category="risk_issue",
            title="Some rows need review before you rely on every detail",
            statement=(
                f"We found {data_quality.duplicate_row_count} possible duplicates, "
                f"{data_quality.invalid_numeric_value_count} invalid numeric values, "
                f"{data_quality.invalid_date_count} invalid dates, "
                f"{data_quality.suspicious_row_count} suspicious rows, and "
                f"{transformation_audit.flagged_row_count} rows flagged during cleaning."
            ),
            why_it_matters=(
                "Data issues can distort revenue, trend, and customer-level takeaways if they are left unresolved."
            ),
            recommended_action=(
                "Review the flagged rows first, especially duplicates, invalid dates, and inconsistent order values."
            ),
            supporting_data={
                "duplicate_row_count": data_quality.duplicate_row_count,
                "invalid_numeric_value_count": data_quality.invalid_numeric_value_count,
                "invalid_date_count": data_quality.invalid_date_count,
                "suspicious_row_count": data_quality.suspicious_row_count,
                "flagged_row_count": transformation_audit.flagged_row_count,
                "missing_required_fields": data_quality.missing_required_fields,
            },
            confidence="high" if not data_quality.missing_required_fields else "medium",
            severity="critical" if affected >= 5 or data_quality.missing_required_fields else "warning",
            evidence_label=f"{affected} data-quality flags detected",
            rank_score=92 + min(affected, 15),
        )

    def _revenue_decline_risk(self, analytics: AnalyticsSummary) -> InsightItem | None:
        trend = analytics.patterns.recent_sales_change
        if analytics.order_count < self.MIN_ORDER_THRESHOLD_FOR_TRENDS:
            return None
        if trend.direction != "down" or trend.percent_change > self.REVENUE_DECLINE_THRESHOLD:
            return None

        change_percent = round(abs(trend.percent_change) * 100, 1)
        return InsightItem(
            category="risk_issue",
            title="Recent sales have declined",
            statement=(
                f"Revenue fell by {change_percent}% in the latest 7-day window, "
                f"dropping from ${trend.previous_period_revenue:,.2f} to ${trend.current_period_revenue:,.2f}."
            ),
            why_it_matters=(
                "A sharp short-term decline can signal weakening demand, missing orders in the export, or an operational issue worth checking quickly."
            ),
            recommended_action=(
                "Confirm the latest orders are present in the source data, then promote your strongest products or investigate recent order issues."
            ),
            supporting_data={
                "previous_period_revenue": trend.previous_period_revenue,
                "current_period_revenue": trend.current_period_revenue,
                "percent_change": trend.percent_change,
            },
            confidence="medium",
            severity="warning",
            evidence_label=f"{change_percent}% recent revenue decline",
            rank_score=85 + min(change_percent / 4, 15),
        )

    def _customer_concentration_risk(self, analytics: AnalyticsSummary) -> InsightItem | None:
        if not analytics.top_customers_by_revenue:
            return None
        top_customer = analytics.top_customers_by_revenue[0]
        if top_customer.revenue_share < self.CUSTOMER_CONCENTRATION_RISK_THRESHOLD:
            return None

        share_percent = round(top_customer.revenue_share * 100, 1)
        return InsightItem(
            category="risk_issue",
            title="Revenue is concentrated in one customer",
            statement=(
                f"{top_customer.label} contributed ${top_customer.revenue:,.2f}, or {share_percent}% of total revenue."
            ),
            why_it_matters=(
                "When too much revenue depends on one customer, a single lost relationship can create a noticeable sales drop."
            ),
            recommended_action=(
                "Retain this customer, but also focus on converting more buyers into repeat customers to reduce concentration risk."
            ),
            supporting_data={
                "customer_identifier": top_customer.label,
                "customer_revenue": top_customer.revenue,
                "customer_revenue_share": top_customer.revenue_share,
            },
            confidence="high",
            severity="warning",
            evidence_label=f"{share_percent}% of revenue came from one customer",
            rank_score=82 + min(share_percent / 5, 18),
        )

    def _follow_up_one_time_buyers_action(self, cleaned_dataset: CleanedDataset) -> InsightItem | None:
        grouped_orders: dict[str, list[float]] = defaultdict(list)
        for row in cleaned_dataset.rows:
            if row.customer_identifier and row.order_total is not None:
                grouped_orders[row.customer_identifier].append(row.order_total)

        one_time_buyers = {
            customer: totals[0]
            for customer, totals in grouped_orders.items()
            if len(totals) == 1 and totals[0] >= self.STRONG_ONE_TIME_BUYER_MIN_SPEND
        }
        if not one_time_buyers:
            return None

        candidate_count = len(one_time_buyers)
        candidate_revenue = round(sum(one_time_buyers.values()), 2)
        return InsightItem(
            category="recommended_action",
            title="Follow up with strong one-time buyers",
            statement=(
                f"{candidate_count} customers placed exactly one order worth at least ${self.STRONG_ONE_TIME_BUYER_MIN_SPEND:,.0f}, "
                f"representing ${candidate_revenue:,.2f} in revenue."
            ),
            why_it_matters=(
                "These customers have already shown strong purchase intent, so they are good candidates for a second-order campaign."
            ),
            recommended_action=(
                "Send a follow-up offer or reminder to these one-time buyers within the next 7 days."
            ),
            supporting_data={
                "candidate_count": candidate_count,
                "candidate_revenue": candidate_revenue,
                "minimum_order_value": self.STRONG_ONE_TIME_BUYER_MIN_SPEND,
            },
            confidence="high",
            severity="info",
            evidence_label=f"{candidate_count} high-value one-time buyers identified",
            rank_score=78 + min(candidate_count * 2, 12),
        )

    def _restock_top_product_action(self, analytics: AnalyticsSummary) -> InsightItem:
        top_product = analytics.top_products_by_revenue[0]
        share_percent = round(top_product.revenue_share * 100, 1)
        return InsightItem(
            category="recommended_action",
            title="Prioritize your top-performing product",
            statement=(
                f"{top_product.label} generated ${top_product.revenue:,.2f}, or {share_percent}% of total revenue."
            ),
            why_it_matters=(
                "A proven top seller is the fastest place to focus inventory and promotion decisions."
            ),
            recommended_action=(
                f"Restock {top_product.label} and feature it prominently in your next email, menu, or promotion."
            ),
            supporting_data={
                "product_name": top_product.label,
                "product_revenue": top_product.revenue,
                "product_revenue_share": top_product.revenue_share,
            },
            confidence="high",
            severity="info",
            evidence_label=f"{top_product.label} is driving {share_percent}% of sales",
            rank_score=84 + min(share_percent / 5, 12),
        )

    def _review_flagged_orders_action(
        self,
        data_quality: DataQualitySummary,
        transformation_audit: TransformationAuditSummary,
    ) -> InsightItem:
        flagged_total = (
            data_quality.duplicate_row_count
            + data_quality.invalid_numeric_value_count
            + data_quality.invalid_date_count
            + data_quality.suspicious_row_count
            + transformation_audit.flagged_row_count
        )
        return InsightItem(
            category="recommended_action",
            title="Review flagged or inconsistent orders first",
            statement=(
                f"{flagged_total} row-level issues were detected across validation and cleaning checks."
            ),
            why_it_matters=(
                "Cleaning up the most problematic rows first will make the rest of your reporting more trustworthy."
            ),
            recommended_action=(
                "Inspect the flagged rows before making inventory, retention, or operational decisions from this upload."
            ),
            supporting_data={
                "flagged_issue_total": flagged_total,
                "flagged_row_count": transformation_audit.flagged_row_count,
            },
            confidence="high",
            severity="warning",
            evidence_label=f"{flagged_total} flagged row issues need review",
            rank_score=90 + min(flagged_total, 10),
        )

    @staticmethod
    def _find_status(
        breakdown: list[StatusBreakdownItem], status_name: str
    ) -> StatusBreakdownItem | None:
        return next((item for item in breakdown if item.status == status_name), None)

    @staticmethod
    def _rank_and_trim(items: list[InsightItem], limit: int) -> list[InsightItem]:
        return sorted(items, key=lambda item: (-item.rank_score, item.title))[:limit]

    @staticmethod
    def _dedupe_actions(items: list[InsightItem]) -> list[InsightItem]:
        seen: set[str] = set()
        deduped: list[InsightItem] = []
        for item in items:
            key = f"{item.title}|{item.evidence_label}"
            if key in seen:
                continue
            seen.add(key)
            deduped.append(item)
        return deduped
