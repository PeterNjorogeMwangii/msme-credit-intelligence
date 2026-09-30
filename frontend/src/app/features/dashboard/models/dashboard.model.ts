export interface RiskBandSummary {
  risk_band: string;
  application_count: number;
  percentage: number;
  average_probability_of_default: number;
}

export interface PortfolioSummary {
  total_assessed_applications: number;
  average_credit_score: number;
  average_probability_of_default: number;
  high_risk_applications: number;
  review_queue_count: number;
  risk_bands: RiskBandSummary[];
}

export interface AssessmentListItem {
  assessment_id: string;
  application_id: string;
  customer_id: string;
  business_name: string;
  requested_amount: number;
  application_status: string;
  assessment_version: number;
  assessment_timestamp: string;
  credit_score: number;
  probability_of_default: number;
  risk_band: string;
  system_recommendation: string;
  recommended_loan_limit: number;
}

export interface AssessmentListResponse {
  items: AssessmentListItem[];
  page: number;
  page_size: number;
  total_items: number;
  total_pages: number;
}

export interface AlertSummary {
  total_alerts: number;
  open_alerts: number;
  acknowledged_alerts: number;
  under_investigation_alerts: number;
  resolved_alerts: number;
  dismissed_alerts: number;
  critical_open_alerts: number;
  high_open_alerts: number;
  unassigned_open_alerts: number;
  affected_customers: number;
}

export interface AlertListItem {
  alert_id: string;
  customer_id: string;
  customer_name?: string;
  loan_id?: string;
  alert_type: string;
  severity: string;
  alert_title: string;
  alert_description: string;
  alert_status: string;
  detected_at: string;
}

export interface AlertListResponse {
  page: number;
  page_size: number;
  total_records: number;
  total_pages: number;
  records: AlertListItem[];
}

export interface DashboardData {
  portfolio: PortfolioSummary;
  highRisk: AssessmentListResponse;
  alertSummary: AlertSummary;
  recentAlerts: AlertListResponse;
}
