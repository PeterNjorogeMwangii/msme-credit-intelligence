import { Component, OnInit, inject, signal } from '@angular/core';
import { CurrencyPipe, DatePipe, DecimalPipe, PercentPipe } from '@angular/common';
import { RouterLink } from '@angular/router';
import { LucideAngularModule } from 'lucide-angular';
import { PortfolioData } from '../../models/portfolio-risk.model';
import { PortfolioRiskService } from '../../services/portfolio-risk.service';

type View='review'|'high-risk'|'recent';
@Component({selector:'app-portfolio-risk-page',imports:[CurrencyPipe,DatePipe,DecimalPipe,PercentPipe,RouterLink,LucideAngularModule],templateUrl:'./portfolio-risk-page.html',styleUrl:'./portfolio-risk-page.scss'})
export class PortfolioRiskPage implements OnInit{
  private readonly service=inject(PortfolioRiskService);readonly data=signal<PortfolioData|null>(null);readonly loading=signal(true);readonly error=signal<string|null>(null);readonly view=signal<View>('review');
  ngOnInit():void{this.load();}load():void{this.loading.set(true);this.error.set(null);this.service.load().subscribe({next:value=>{this.data.set(value);this.loading.set(false);},error:error=>{console.error('Portfolio API error',error);this.error.set('Portfolio risk data could not be retrieved from FastAPI.');this.loading.set(false);}});}
  select(value:View):void{this.view.set(value);}label(value:string):string{return value.replaceAll('_',' ');}tone(value:string):string{return value.toLowerCase().replaceAll('_','-');}
}
