export interface RiskBandSummary{risk_band:string;application_count:number;percentage:number;average_probability_of_default:number;}
export interface PortfolioSummary{total_assessed_applications:number;average_credit_score:number;average_probability_of_default:number;high_risk_applications:number;review_queue_count:number;risk_bands:RiskBandSummary[];}
export interface ProbabilityBucket{bucket:string;lower_bound:number;upper_bound:number;application_count:number;percentage:number;}
export interface Distribution{total_applications:number;buckets:ProbabilityBucket[];}
export interface AssessmentItem{assessment_id:string;application_id:string;customer_id:string;business_name:string;requested_amount:number;application_status:string;assessment_timestamp:string;credit_score:number;probability_of_default:number;risk_band:string;system_recommendation:string;recommended_loan_limit:number;}
export interface AssessmentPage{items:AssessmentItem[];page:number;page_size:number;total_items:number;total_pages:number;}
export interface RecentItem{assessment_id:string;application_id:string;customer_id:string;business_name:string;assessment_timestamp:string;credit_score:number;probability_of_default:number;risk_band:string;system_recommendation:string;}
export interface PortfolioData{summary:PortfolioSummary;distribution:Distribution;reviewQueue:AssessmentPage;highRisk:AssessmentPage;recent:RecentItem[];}
