import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, forkJoin } from 'rxjs';
import {
  AlertListResponse,
  AlertSummary,
  AssessmentListResponse,
  DashboardData,
  PortfolioSummary
} from '../models/dashboard.model';

@Injectable({ providedIn: 'root' })
export class DashboardService {
  private readonly http = inject(HttpClient);
  private readonly api = '/api/v1';

  loadDashboard(): Observable<DashboardData> {
    return forkJoin({
      portfolio: this.http.get<PortfolioSummary>(`${this.api}/credit-risk/portfolio/summary`),
      highRisk: this.http.get<AssessmentListResponse>(`${this.api}/credit-risk/high-risk-customers`, {
        params: new HttpParams().set('page', 1).set('page_size', 5)
      }),
      alertSummary: this.http.get<AlertSummary>(`${this.api}/alerts/summary`),
      recentAlerts: this.http.get<AlertListResponse>(`${this.api}/alerts`, {
        params: new HttpParams().set('page', 1).set('page_size', 4)
      })
    });
  }
}
