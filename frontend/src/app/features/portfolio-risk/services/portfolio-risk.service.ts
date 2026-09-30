import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, forkJoin } from 'rxjs';
import { AssessmentPage, Distribution, PortfolioData, PortfolioSummary, RecentItem } from '../models/portfolio-risk.model';

@Injectable({providedIn:'root'})
export class PortfolioRiskService{
  private readonly http=inject(HttpClient);private readonly api='/api/v1/credit-risk';
  load():Observable<PortfolioData>{const pageParams=new HttpParams().set('page',1).set('page_size',8);return forkJoin({summary:this.http.get<PortfolioSummary>(`${this.api}/portfolio/summary`),distribution:this.http.get<Distribution>(`${this.api}/portfolio/distribution`),reviewQueue:this.http.get<AssessmentPage>(`${this.api}/review-queue`,{params:pageParams}),highRisk:this.http.get<AssessmentPage>(`${this.api}/high-risk-customers`,{params:pageParams}),recent:this.http.get<RecentItem[]>(`${this.api}/recent-activity`,{params:new HttpParams().set('limit',8)})});}
}
