import { Component, OnInit, inject, signal } from '@angular/core';
import { DatePipe, DecimalPipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { LucideAngularModule } from 'lucide-angular';
import { CustomerListItem } from '../../models/customer.model';
import { CustomerService } from '../../services/customer.service';

@Component({ selector: 'app-customer-list-page', imports: [DatePipe, DecimalPipe, FormsModule, RouterLink, LucideAngularModule], templateUrl: './customer-list-page.html', styleUrl: './customer-list-page.scss' })
export class CustomerListPage implements OnInit {
  private readonly service = inject(CustomerService);
  readonly records = signal<CustomerListItem[]>([]); readonly loading = signal(true);
  readonly error = signal<string | null>(null); readonly totalRecords = signal(0); readonly totalPages = signal(0);
  page = 1; pageSize = 20; search = ''; status = '';
  ngOnInit(): void { this.load(); }
  load(): void { this.loading.set(true); this.error.set(null); this.service.list(this.page, this.pageSize, this.search, this.status).subscribe({ next: result => { this.records.set(result.records); this.totalRecords.set(result.total_records); this.totalPages.set(result.total_pages); this.loading.set(false); }, error: error => { console.error('Customer API error', error); this.error.set('Customers could not be retrieved from FastAPI.'); this.loading.set(false); } }); }
  applyFilters(): void { this.page = 1; this.load(); } clearFilters(): void { this.search = ''; this.status = ''; this.page = 1; this.load(); }
  previous(): void { if (this.page > 1) { this.page--; this.load(); } } next(): void { if (this.page < this.totalPages()) { this.page++; this.load(); } }
  displayName(item: CustomerListItem): string { return item.trading_name || item.legal_name || item.customer_id; }
  initials(item: CustomerListItem): string { return this.displayName(item).split(/\s+/).slice(0, 2).map(v => v[0]).join('').toUpperCase(); }
  tone(value?: string): string { return (value || 'UNKNOWN').toLowerCase().replaceAll('_', '-'); }
}
