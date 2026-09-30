export interface AuthUser {
  user_id: string;
  username: string;
  email: string;
  full_name: string;
  role_code: string;
  employee_number: string | null;
  branch_code: string | null;
  account_status: string;
  last_login_at: string | null;
}

export interface LoginResponse {
  access_token: string;
  token_type: 'bearer';
  expires_in: number;
  user: AuthUser;
}
