export interface CustomerListItem { customer_id: string; legal_name?: string; trading_name?: string; record_status?: string; aml_risk_classification?: string; created_at?: string; updated_at?: string; }
export interface CustomerListResponse { page: number; page_size: number; total_records: number; total_pages: number; records: CustomerListItem[]; }

export interface CustomerProfile extends CustomerListItem {
  customer_number?: string; customer_type?: string; registration_number?: string;
  tax_identifier?: string; business_type?: string; industry_code?: string;
  industry_description?: string; incorporation_date?: string;
  relationship_start_date?: string; employee_count?: number;
  annual_turnover_declared?: number; turnover_currency?: string;
  county_code?: string; branch_code?: string; relationship_manager_id?: string;
  kyc_status?: string; kyc_review_date?: string; pep_flag?: boolean;
  sanctions_match_flag?: boolean;
}
export interface FinancialSummary {
  account_count: number; active_account_count: number; estimated_total_balance: number;
  transaction_count_180d: number; total_credits_180d: number; total_debits_180d: number;
  net_cash_flow_180d: number; average_transaction_amount_180d: number;
  cash_transaction_count_180d: number; application_count: number;
  approved_application_count: number; declined_application_count: number;
  total_requested_amount: number; loan_count: number; active_loan_count: number;
  total_original_principal: number; total_outstanding_principal: number;
  total_arrears: number; maximum_days_past_due: number;
  scheduled_installment_count: number; overdue_installment_count: number;
  scheduled_amount_due: number; scheduled_amount_paid: number;
  scheduled_outstanding_amount: number;
}
export interface RiskSummary {
  current_credit_score?: number; probability_of_default?: number; current_risk_band?: string;
  system_recommendation?: string; latest_assessment_at?: string; bureau_score?: number;
  bureau_max_dpd_12m?: number; bureau_delinquent_facilities: number;
  bureau_written_off_facilities: number; bureau_legal_cases: number;
  adverse_listing_flag: boolean; open_alert_count: number; high_alert_count: number;
  critical_alert_count: number;
}
export type DataRecord = Record<string, any>;
export interface Customer360Response {
  customer: CustomerProfile; financial_summary: FinancialSummary; risk_summary: RiskSummary;
  accounts: DataRecord[]; recent_transactions: DataRecord[]; loan_applications: DataRecord[];
  loans: DataRecord[]; risk_alerts: DataRecord[]; activity_timeline: DataRecord[];
}
