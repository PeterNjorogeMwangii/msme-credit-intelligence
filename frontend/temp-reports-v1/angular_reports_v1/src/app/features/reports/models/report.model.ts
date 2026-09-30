export interface PortfolioSummary{total_assessed_applications:number;average_credit_score:number;average_probability_of_default:number;high_risk_applications:number;review_queue_count:number;risk_bands:Record<string,unknown>[];}
export interface CustomerPage{page:number;page_size:number;total_records:number;total_pages:number;records:Record<string,unknown>[];}
export interface AssessmentPage{page:number;page_size:number;total_items:number;total_pages:number;items:Record<string,unknown>[];}
export interface AlertPage{page:number;page_size:number;total_records:number;total_pages:number;records:Record<string,unknown>[];}
export interface AlertSummary{total_alerts:number;open_alerts:number;acknowledged_alerts:number;under_investigation_alerts:number;resolved_alerts:number;dismissed_alerts:number;critical_open_alerts:number;high_open_alerts:number;unassigned_open_alerts:number;affected_customers:number;}
export interface ReportOverview{portfolio:PortfolioSummary;customers:CustomerPage;assessments:AssessmentPage;alerts:AlertSummary;}
