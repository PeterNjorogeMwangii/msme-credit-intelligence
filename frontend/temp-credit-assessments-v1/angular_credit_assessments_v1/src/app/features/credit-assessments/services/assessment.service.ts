import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { AssessmentDetail, AssessmentListResponse } from '../models/assessment.model';

@Injectable({providedIn:'root'})
export class AssessmentService {
  private readonly http=inject(HttpClient); private readonly api='/api/v1/credit-risk';
  list(page:number,pageSize:number,search?:string,riskBand?:string,recommendation?:string):Observable<AssessmentListResponse>{let params=new HttpParams().set('page',page).set('page_size',pageSize);if(search?.trim())params=params.set('search',search.trim());if(riskBand)params=params.set('risk_band',riskBand);if(recommendation)params=params.set('recommendation',recommendation);return this.http.get<AssessmentListResponse>(`${this.api}/assessments`,{params});}
  latest(applicationId:string):Observable<AssessmentDetail>{return this.http.get<AssessmentDetail>(`${this.api}/applications/${encodeURIComponent(applicationId)}/latest`);}
  score(applicationId:string):Observable<AssessmentDetail>{return this.http.post<AssessmentDetail>(`${this.api}/applications/${encodeURIComponent(applicationId)}/score`,{});}
}
