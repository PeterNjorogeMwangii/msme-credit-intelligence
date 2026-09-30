import { HttpClient } from '@angular/common/http';
import { Injectable, computed, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { Observable, tap } from 'rxjs';
import { AuthUser, LoginResponse } from './auth.models';

const TOKEN_KEY = 'msme_access_token';
const USER_KEY = 'msme_auth_user';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly http = inject(HttpClient);
  private readonly router = inject(Router);
  private readonly userState = signal<AuthUser | null>(this.readUser());

  readonly user = this.userState.asReadonly();
  readonly authenticated = computed(() => !!this.token && !!this.userState());

  get token(): string | null {
    return localStorage.getItem(TOKEN_KEY);
  }

  login(username: string, password: string): Observable<LoginResponse> {
    return this.http
      .post<LoginResponse>('/api/v1/auth/login', { username, password })
      .pipe(tap((response) => this.storeSession(response)));
  }

  refreshUser(): Observable<AuthUser> {
    return this.http.get<AuthUser>('/api/v1/auth/me').pipe(
      tap((user) => {
        localStorage.setItem(USER_KEY, JSON.stringify(user));
        this.userState.set(user);
      })
    );
  }

  hasAnyRole(...roles: string[]): boolean {
    return roles.includes(this.userState()?.role_code ?? '');
  }

  logout(redirect = true): void {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    this.userState.set(null);
    if (redirect) void this.router.navigate(['/login']);
  }

  private storeSession(response: LoginResponse): void {
    localStorage.setItem(TOKEN_KEY, response.access_token);
    localStorage.setItem(USER_KEY, JSON.stringify(response.user));
    this.userState.set(response.user);
  }

  private readUser(): AuthUser | null {
    const value = localStorage.getItem(USER_KEY);
    if (!value) return null;
    try {
      return JSON.parse(value) as AuthUser;
    } catch {
      localStorage.removeItem(USER_KEY);
      return null;
    }
  }
}
