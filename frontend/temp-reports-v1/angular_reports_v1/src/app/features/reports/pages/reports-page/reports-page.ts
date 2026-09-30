import { Component, OnInit, inject, signal } from '@angular/core';
import { DatePipe, DecimalPipe, PercentPipe } from '@angular/common';
import { LucideAngularModule } from 'lucide-angular';
import { Observable } from 'rxjs';
import { ReportOverview } from '../../models/report.model';
import { ReportService } from '../../services/report.service';

type ReportType='portfolio'|'customers'|'assessments'|'alerts';
@Component({selector:'app-reports-page',imports:[DatePipe,DecimalPipe,PercentPipe,LucideAngularModule],templateUrl:'./reports-page.html',styleUrl:'./reports-page.scss'})
export class ReportsPage implements OnInit{
  private readonly service=inject(ReportService);readonly overview=signal<ReportOverview|null>(null);readonly loading=signal(true);readonly error=signal<string|null>(null);readonly exporting=signal<ReportType|null>(null);readonly message=signal<string|null>(null);readonly generatedAt=signal(new Date());
  ngOnInit():void{this.load();}load():void{this.loading.set(true);this.error.set(null);this.service.overview().subscribe({next:value=>{this.overview.set(value);this.generatedAt.set(new Date());this.loading.set(false);},error:e=>{console.error(e);this.error.set('Report data could not be retrieved from FastAPI.');this.loading.set(false);}});}
  export(type:ReportType):void{const o=this.overview();if(!o)return;this.exporting.set(type);this.message.set(null);let request:Observable<Record<string,unknown>[]>;if(type==='customers')request=this.service.allCustomers();else if(type==='assessments')request=this.service.allAssessments();else if(type==='alerts')request=this.service.allAlerts();else request=new Observable(subscriber=>{subscriber.next(this.service.portfolioRows(o.portfolio));subscriber.complete();});request.subscribe({next:rows=>{this.download(`${type}_report_${this.dateStamp()}.csv`,rows);this.message.set(`${rows.length.toLocaleString()} ${type} report rows exported.`);this.exporting.set(null);},error:e=>{console.error(e);this.message.set(`The ${type} report could not be exported.`);this.exporting.set(null);}});}
  private download(filename:string,rows:Record<string,unknown>[]):void{if(!rows.length)return;const columns=Array.from(new Set(rows.flatMap(row=>Object.keys(row))));const escape=(value:unknown)=>{const text=value===null||value===undefined?'':typeof value==='object'?JSON.stringify(value):String(value);return `"${text.replaceAll('"','""')}"`;};const csv=[columns.map(escape).join(','),...rows.map(row=>columns.map(column=>escape(row[column])).join(','))].join('\r\n');const url=URL.createObjectURL(new Blob(['\uFEFF'+csv],{type:'text/csv;charset=utf-8'}));const link=document.createElement('a');link.href=url;link.download=filename;link.click();URL.revokeObjectURL(url);}
  private dateStamp():string{return new Date().toISOString().slice(0,10);}
}
