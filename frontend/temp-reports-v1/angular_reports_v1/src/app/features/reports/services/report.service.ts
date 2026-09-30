import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, forkJoin, map, of, switchMap } from 'rxjs';
import { AlertPage, AlertSummary, AssessmentPage, CustomerPage, PortfolioSummary, ReportOverview } from '../models/report.model';

@Injectable({providedIn:'root'})
export class ReportService{
  private readonly http=inject(HttpClient);private readonly api='/api/v1';private params(page:number){return new HttpParams().set('page',page).set('page_size',100);}
  overview():Observable<ReportOverview>{return forkJoin({portfolio:this.http.get<PortfolioSummary>(`${this.api}/credit-risk/portfolio/summary`),customers:this.http.get<CustomerPage>(`${this.api}/customers`,{params:new HttpParams().set('page',1).set('page_size',1)}),assessments:this.http.get<AssessmentPage>(`${this.api}/credit-risk/assessments`,{params:new HttpParams().set('page',1).set('page_size',1)}),alerts:this.http.get<AlertSummary>(`${this.api}/alerts/summary`)});}
  allCustomers():Observable<Record<string,unknown>[]>{return this.http.get<CustomerPage>(`${this.api}/customers`,{params:this.params(1)}).pipe(switchMap(first=>{if(first.total_pages<=1)return of(first.records);const calls=Array.from({length:first.total_pages-1},(_,i)=>this.http.get<CustomerPage>(`${this.api}/customers`,{params:this.params(i+2)}));return forkJoin(calls).pipe(map(pages=>[...first.records,...pages.flatMap(p=>p.records)]));}));}
  allAssessments():Observable<Record<string,unknown>[]>{return this.http.get<AssessmentPage>(`${this.api}/credit-risk/assessments`,{params:this.params(1)}).pipe(switchMap(first=>{if(first.total_pages<=1)return of(first.items);const calls=Array.from({length:first.total_pages-1},(_,i)=>this.http.get<AssessmentPage>(`${this.api}/credit-risk/assessments`,{params:this.params(i+2)}));return forkJoin(calls).pipe(map(pages=>[...first.items,...pages.flatMap(p=>p.items)]));}));}
  allAlerts():Observable<Record<string,unknown>[]>{return this.http.get<AlertPage>(`${this.api}/alerts`,{params:this.params(1)}).pipe(switchMap(first=>{if(first.total_pages<=1)return of(first.records);const calls=Array.from({length:first.total_pages-1},(_,i)=>this.http.get<AlertPage>(`${this.api}/alerts`,{params:this.params(i+2)}));return forkJoin(calls).pipe(map(pages=>[...first.records,...pages.flatMap(p=>p.records)]));}));}
  portfolioRows(summary:PortfolioSummary):Record<string,unknown>[]{return summary.risk_bands.map(b=>({...b,total_assessed_applications:summary.total_assessed_applications,average_credit_score:summary.average_credit_score,portfolio_average_pd:summary.average_probability_of_default,high_risk_applications:summary.high_risk_applications,review_queue_count:summary.review_queue_count}));}
}
