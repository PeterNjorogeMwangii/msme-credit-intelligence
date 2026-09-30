export interface TransactionOverview { date_from:string; date_to:string; transaction_count:number; total_credits:number; total_debits:number; net_cash_flow:number; average_transaction_amount:number; cash_transaction_count:number; high_value_transaction_count:number; active_customer_count:number; }
export interface TrendPoint { period:string; credits:number; debits:number; net_cash_flow:number; transaction_count:number; }
export interface BreakdownItem { code:string; transaction_count:number; total_amount:number; percentage:number; }
export interface TransactionAnalytics { overview:TransactionOverview; trend:TrendPoint[]; categories:BreakdownItem[]; channels:BreakdownItem[]; }
export interface TransactionItem { transaction_id:string; account_id:string; customer_id:string; customer_name:string; posting_timestamp:string; transaction_category:string; credit_debit_indicator:'C'|'D'; local_currency_amount:number; currency_code:string; channel_code:string; transaction_description:string|null; cash_transaction_flag:boolean; high_value_flag:boolean; }
export interface TransactionList { page:number; page_size:number; total_records:number; total_pages:number; records:TransactionItem[]; }
export interface TransactionFilters { days:number; customer_id:string; account_id:string; direction:string; category:string; channel:string; search:string; high_value_only:boolean; }
