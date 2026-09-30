import { Component, OnInit, inject, signal } from '@angular/core';
import { CurrencyPipe, DatePipe, DecimalPipe, PercentPipe } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { LucideAngularModule } from 'lucide-angular';
import { Customer360Response } from '../../models/customer.model';
import { CustomerService } from '../../services/customer.service';
import { RecordTable } from '../../components/record-table/record-table';

type Tab = 'overview'|'accounts'|'transactions'|'applications'|'loans'|'alerts'|'activity';
@Component({ selector:'app-customer-360-page', imports:[CurrencyPipe,DatePipe,DecimalPipe,PercentPipe,RouterLink,LucideAngularModule,RecordTable], templateUrl:'./customer-360-page.html', styleUrl:'./customer-360-page.scss' })
export class Customer360Page implements OnInit {
  private readonly route=inject(ActivatedRoute); private readonly service=inject(CustomerService);
  readonly data=signal<Customer360Response|null>(null); readonly loading=signal(true); readonly error=signal<string|null>(null); readonly activeTab=signal<Tab>('overview');
  ngOnInit():void{this.load();}
  load():void{const id=this.route.snapshot.paramMap.get('customerId');if(!id){this.error.set('Customer ID is missing.');this.loading.set(false);return;}this.loading.set(true);this.error.set(null);this.service.get360(id).subscribe({next:value=>{this.data.set(value);this.loading.set(false);},error:error=>{console.error('Customer 360 API error',error);this.error.set(error.status===404?'Customer was not found.':'Customer 360 could not be loaded from FastAPI.');this.loading.set(false);}});}
  tab(value:Tab):void{this.activeTab.set(value);} tone(value?:string):string{return(value||'unknown').toLowerCase().replaceAll('_','-');}
  name(data:Customer360Response):string{return data.customer.trading_name||data.customer.legal_name||data.customer.customer_id;}
}
