import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { Customer360Response, CustomerListResponse } from '../models/customer.model';

@Injectable({ providedIn: 'root' })
export class CustomerService {
  private readonly http = inject(HttpClient);
  private readonly endpoint = '/api/v1/customers';
  list(page: number, pageSize: number, search?: string, status?: string): Observable<CustomerListResponse> {
    let params = new HttpParams().set('page', page).set('page_size', pageSize);
    if (search?.trim()) params = params.set('search', search.trim());
    if (status) params = params.set('customer_status', status);
    return this.http.get<CustomerListResponse>(this.endpoint, { params });
  }
  get360(customerId: string): Observable<Customer360Response> {
    return this.http.get<Customer360Response>(`${this.endpoint}/${encodeURIComponent(customerId)}`);
  }
}
