import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, forkJoin } from 'rxjs';
import { AlertFilters, AlertItem, AlertList, AlertSummary } from '../models/alert.model';

@Injectable({providedIn:'root'})
export class AlertService{
  private readonly http=inject(HttpClient);private readonly api='/api/v1/alerts';
  load(filters:AlertFilters):Observable<{summary:AlertSummary;list:AlertList}>{let params=new HttpParams().set('page',filters.page).set('page_size',filters.pageSize);if(filters.search?.trim())params=params.set('search',filters.search.trim());if(filters.status)params=params.set('alert_status',filters.status);if(filters.severity)params=params.set('severity',filters.severity);if(filters.alertType)params=params.set('alert_type',filters.alertType);if(filters.unassigned)params=params.set('unassigned',true);return forkJoin({summary:this.http.get<AlertSummary>(`${this.api}/summary`),list:this.http.get<AlertList>(this.api,{params})});}
  detail(id:string):Observable<AlertItem>{return this.http.get<AlertItem>(`${this.api}/${id}`);}acknowledge(id:string,assignedTo:string|null=null):Observable<AlertItem>{return this.http.patch<AlertItem>(`${this.api}/${id}/acknowledge`,{assigned_to:assignedTo||null});}
  assign(id:string,assignedTo:string):Observable<AlertItem>{return this.http.patch<AlertItem>(`${this.api}/${id}/assign`,{assigned_to:assignedTo,move_to_investigation:true});}
  resolve(id:string,notes:string,resolution:'RESOLVED'|'DISMISSED'):Observable<AlertItem>{return this.http.patch<AlertItem>(`${this.api}/${id}/resolve`,{resolution_notes:notes,resolution});}
}
