export type Severity = "info" | "warning" | "critical";
export type Confidence = "high" | "medium" | "low";

export interface QualityIssue {
  code: string;
  severity: Severity;
  message: string;
  affected_count?: number | null;
}

export interface DataQualitySummary {
  missing_required_fields: string[];
  missing_value_counts: Record<string, number>;
  duplicate_row_count: number;
  invalid_numeric_value_count: number;
  invalid_date_count: number;
  suspicious_row_count: number;
  issues: QualityIssue[];
}

export interface CanonicalOrderRow {
  row_number: number;
  order_id?: string | null;
  customer_identifier?: string | null;
  product_name?: string | null;
  quantity?: number | null;
  order_total?: number | null;
  order_date?: string | null;
  fulfillment_status: string;
  payment_status: string;
  original_values: Record<string, string>;
  flags: string[];
}

export interface CleanedDataset {
  canonical_schema_version: string;
  row_count: number;
  rows: CanonicalOrderRow[];
}

export interface TransformationAuditSummary {
  total_changes: number;
  flagged_row_count: number;
  field_change_counts: Record<string, number>;
  entries: Array<{
    row_number: number;
    field: string;
    action: string;
    original_value?: string | null;
    cleaned_value?: string | number | null;
    note: string;
  }>;
}

export interface RankedMetricItem {
  label: string;
  revenue: number;
  order_count: number;
  revenue_share: number;
}

export interface StatusBreakdownItem {
  status: string;
  count: number;
  share: number;
}

export interface TimeSeriesPoint {
  date: string;
  revenue: number;
  order_count: number;
}

export interface CategorySeriesPoint {
  label: string;
  revenue: number;
  order_count: number;
}

export interface StatusSeriesPoint {
  status_type: "fulfillment" | "payment";
  status: string;
  count: number;
}

export interface AnalyticsSummary {
  total_revenue: { value: number; formatted_value: string };
  order_count: number;
  average_order_value: { value: number; formatted_value: string };
  repeat_customer_count: number;
  repeat_customer_rate: number;
  top_products_by_revenue: RankedMetricItem[];
  top_customers_by_revenue: RankedMetricItem[];
  fulfillment_status_breakdown: StatusBreakdownItem[];
  payment_status_breakdown: StatusBreakdownItem[];
  charts: {
    sales_over_time: TimeSeriesPoint[];
    revenue_by_product: CategorySeriesPoint[];
    top_customers: CategorySeriesPoint[];
    status_breakdown: StatusSeriesPoint[];
  };
  patterns: {
    revenue_trend: {
      direction: string;
      absolute_change: number;
      percent_change: number;
      current_period_revenue: number;
      previous_period_revenue: number;
      summary: string;
    };
    recent_sales_change: {
      direction: string;
      absolute_change: number;
      percent_change: number;
      current_period_revenue: number;
      previous_period_revenue: number;
      summary: string;
    };
    revenue_concentration: {
      top_product_share: number;
      top_three_product_share: number;
      repeat_customer_revenue_share: number;
      summary: string;
    };
  };
}

export interface InsightItem {
  category: "key_win" | "risk_issue" | "recommended_action";
  title: string;
  statement: string;
  why_it_matters: string;
  recommended_action: string;
  supporting_data: Record<string, unknown>;
  confidence: Confidence;
  severity: Severity;
  evidence_label: string;
  rank_score: number;
}

export interface InsightPayload {
  key_wins: InsightItem[];
  risks_issues: InsightItem[];
  recommended_actions: InsightItem[];
  suppressed_due_to_small_dataset: boolean;
  total_generated: number;
}

export interface OwnerMessage {
  level: "success" | "warning" | "error";
  title: string;
  detail: string;
}

export interface UploadResponse {
  status: "success" | "warning" | "error";
  data_quality: DataQualitySummary;
  cleaned_dataset: CleanedDataset;
  transformation_audit: TransformationAuditSummary;
  analytics: AnalyticsSummary;
  insights: InsightPayload;
  owner_messages: OwnerMessage[];
}
