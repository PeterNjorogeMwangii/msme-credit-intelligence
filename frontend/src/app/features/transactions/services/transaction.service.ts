import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { TransactionAnalytics, TransactionFilters, TransactionList } from '../models/transaction.models';

@Injectable({ providedIn:'root' })
export class TransactionService {
  private readonly http=inject(HttpClient);
  private params(filters:TransactionFilters):HttpParams {
    let params=new HttpParams().set('days',filters.days).set('high_value_only',filters.high_value_only);
    for(const key of ['customer_id','account_id','direction','category','channel','search'] as const){ if(filters[key]) params=params.set(key,filters[key]); }
    return params;
  }
  analytics(filters:TransactionFilters){ return this.http.get<TransactionAnalytics>('/api/v1/transactions/analytics',{params:this.params(filters)}); }
  list(filters:TransactionFilters,page:number,pageSize:number){ return this.http.get<TransactionList>('/api/v1/transactions',{params:this.params(filters).set('page',page).set('page_size',pageSize)}); }
  export(filters:TransactionFilters){ return this.http.get('/api/v1/transactions/export.csv',{params:this.params(filters),responseType:'blob'}); }
}
