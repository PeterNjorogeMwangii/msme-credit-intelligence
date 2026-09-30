export interface UserItem{user_id:string;username:string;email:string;full_name:string;role_code:string;employee_number?:string;branch_code?:string;account_status:string;failed_login_attempts:number;last_login_at?:string;created_at:string;updated_at:string;}
export interface UserPage{page:number;page_size:number;total_records:number;total_pages:number;records:UserItem[];}
export interface AuditItem{audit_id:string;user_id?:string;actor_name?:string;action:string;entity_type:string;entity_id:string;previous_value?:Record<string,unknown>;new_value?:Record<string,unknown>;reason?:string;ip_address?:string;user_agent?:string;correlation_id:string;action_timestamp:string;}
export interface AuditPage{page:number;page_size:number;total_records:number;total_pages:number;records:AuditItem[];}
export interface AdminSummary{total_users:number;active_users:number;locked_users:number;disabled_users:number;failed_login_attempts:number;audit_events_24h:number;}
