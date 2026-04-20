from typing import Literal

from pydantic import BaseModel, Field


class MetricValue(BaseModel):
    value: float
    formatted_value: str


class RankedMetricItem(BaseModel):
    label: str
    revenue: float
    order_count: int
    revenue_share: float


class StatusBreakdownItem(BaseModel):
    status: str
    count: int
    share: float


class TimeSeriesPoint(BaseModel):
    date: str
    revenue: float
    order_count: int


class CategorySeriesPoint(BaseModel):
    label: str
    revenue: float
    order_count: int


class StatusSeriesPoint(BaseModel):
    status_type: Literal["fulfillment", "payment"]
    status: str
    count: int


class RevenueTrendSummary(BaseModel):
    direction: Literal["up", "down", "flat", "insufficient_data"]
    absolute_change: float = 0.0
    percent_change: float = 0.0
    current_period_revenue: float = 0.0
    previous_period_revenue: float = 0.0
    summary: str


class RevenueConcentrationSummary(BaseModel):
    top_product_share: float = 0.0
    top_three_product_share: float = 0.0
    repeat_customer_revenue_share: float = 0.0
    summary: str


class BusinessPatternSummary(BaseModel):
    revenue_trend: RevenueTrendSummary
    recent_sales_change: RevenueTrendSummary
    revenue_concentration: RevenueConcentrationSummary


class ChartAggregates(BaseModel):
    sales_over_time: list[TimeSeriesPoint] = Field(default_factory=list)
    revenue_by_product: list[CategorySeriesPoint] = Field(default_factory=list)
    top_customers: list[CategorySeriesPoint] = Field(default_factory=list)
    status_breakdown: list[StatusSeriesPoint] = Field(default_factory=list)


class AnalyticsSummary(BaseModel):
    total_revenue: MetricValue
    order_count: int
    average_order_value: MetricValue
    repeat_customer_count: int
    repeat_customer_rate: float
    top_products_by_revenue: list[RankedMetricItem] = Field(default_factory=list)
    top_customers_by_revenue: list[RankedMetricItem] = Field(default_factory=list)
    fulfillment_status_breakdown: list[StatusBreakdownItem] = Field(default_factory=list)
    payment_status_breakdown: list[StatusBreakdownItem] = Field(default_factory=list)
    charts: ChartAggregates
    patterns: BusinessPatternSummary
