import { Component, OnInit, inject, signal } from '@angular/core';
import { CurrencyPipe, DatePipe, DecimalPipe, PercentPipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { LucideAngularModule } from 'lucide-angular';
import { AssessmentListItem } from '../../models/assessment.model';
import { AssessmentService } from '../../services/assessment.service';

@Component({selector:'app-assessment-list-page',imports:[CurrencyPipe,DatePipe,DecimalPipe,PercentPipe,FormsModule,RouterLink,LucideAngularModule],templateUrl:'./assessment-list-page.html',styleUrl:'./assessment-list-page.scss'})
export class AssessmentListPage implements OnInit {
  private readonly service=inject(AssessmentService);readonly records=signal<AssessmentListItem[]>([]);readonly loading=signal(true);readonly error=signal<string|null>(null);readonly total=signal(0);readonly pages=signal(0);
  page=1;pageSize=20;search='';riskBand='';recommendation='';
  ngOnInit():void{this.load();}load():void{this.loading.set(true);this.error.set(null);this.service.list(this.page,this.pageSize,this.search,this.riskBand,this.recommendation).subscribe({next:r=>{this.records.set(r.items);this.total.set(r.total_items);this.pages.set(r.total_pages);this.loading.set(false);},error:e=>{console.error(e);this.error.set('Credit assessments could not be retrieved from FastAPI.');this.loading.set(false);}});}
  apply():void{this.page=1;this.load();}clear():void{this.search='';this.riskBand='';this.recommendation='';this.page=1;this.load();}previous():void{if(this.page>1){this.page--;this.load();}}next():void{if(this.page<this.pages()){this.page++;this.load();}}
  label(value:string):string{return value.replaceAll('_',' ');}tone(value:string):string{return value.toLowerCase().replaceAll('_','-');}
}
