import { CurrencyPipe, DatePipe, DecimalPipe } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { LucideAngularModule } from 'lucide-angular';
import { forkJoin } from 'rxjs';
import { TransactionAnalytics, TransactionFilters, TransactionList } from '../../models/transaction.models';
import { TransactionService } from '../../services/transaction.service';

@Component({selector:'app-transaction-analytics-page',imports:[FormsModule,RouterLink,LucideAngularModule,CurrencyPipe,DatePipe,DecimalPipe],templateUrl:'./transaction-analytics-page.html',styleUrl:'./transaction-analytics-page.scss'})
export class TransactionAnalyticsPage implements OnInit {
  private readonly service=inject(TransactionService);
  readonly loading=signal(true); readonly exporting=signal(false); readonly error=signal('');
  readonly analytics=signal<TransactionAnalytics|null>(null); readonly list=signal<TransactionList|null>(null);
  filters:TransactionFilters={days:180,customer_id:'',account_id:'',direction:'',category:'',channel:'',search:'',high_value_only:false};
  page=1; readonly pageSize=20;
  ngOnInit(){this.load();}
  load(resetPage=false){if(resetPage)this.page=1;this.loading.set(true);this.error.set('');forkJoin({analytics:this.service.analytics(this.filters),list:this.service.list(this.filters,this.page,this.pageSize)}).subscribe({next:r=>{this.analytics.set(r.analytics);this.list.set(r.list);this.loading.set(false);},error:e=>{this.error.set(e.error?.detail||'Unable to load transaction analytics.');this.loading.set(false);}});}
  reset(){this.filters={days:180,customer_id:'',account_id:'',direction:'',category:'',channel:'',search:'',high_value_only:false};this.load(true);}
  go(page:number){if(page<1||page>(this.list()?.total_pages||0))return;this.page=page;this.load();}
  maxTrend():number{return Math.max(1,...(this.analytics()?.trend||[]).flatMap(p=>[Number(p.credits),Number(p.debits)]));}
  export(){this.exporting.set(true);this.service.export(this.filters).subscribe({next:blob=>{const url=URL.createObjectURL(blob);const anchor=document.createElement('a');anchor.href=url;anchor.download='transaction_analytics.csv';anchor.click();URL.revokeObjectURL(url);this.exporting.set(false);},error:()=>{this.error.set('CSV export failed.');this.exporting.set(false);}});}
}
