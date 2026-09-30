import { Component, OnInit, inject, signal } from '@angular/core';
import { CurrencyPipe, DatePipe, DecimalPipe, PercentPipe } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { LucideAngularModule } from 'lucide-angular';
import { AssessmentDetail, Factor } from '../../models/assessment.model';
import { AssessmentService } from '../../services/assessment.service';

@Component({selector:'app-assessment-detail-page',imports:[CurrencyPipe,DatePipe,DecimalPipe,PercentPipe,RouterLink,LucideAngularModule],templateUrl:'./assessment-detail-page.html',styleUrl:'./assessment-detail-page.scss'})
export class AssessmentDetailPage implements OnInit {
  private readonly route=inject(ActivatedRoute);private readonly service=inject(AssessmentService);readonly assessment=signal<AssessmentDetail|null>(null);readonly loading=signal(true);readonly scoring=signal(false);readonly error=signal<string|null>(null);readonly message=signal<string|null>(null);applicationId='';
  ngOnInit():void{this.applicationId=this.route.snapshot.paramMap.get('applicationId')||'';this.load();}
  load():void{this.loading.set(true);this.error.set(null);this.service.latest(this.applicationId).subscribe({next:a=>{this.assessment.set(a);this.loading.set(false);},error:e=>{this.error.set(e.status===404?'No assessment exists for this application.':'The assessment could not be loaded.');this.loading.set(false);}});}
  rescore():void{this.scoring.set(true);this.message.set(null);this.service.score(this.applicationId).subscribe({next:a=>{this.assessment.set(a);this.message.set(`Assessment version ${a.assessment_version} created successfully.`);this.scoring.set(false);},error:e=>{console.error(e);this.message.set('The application could not be rescored.');this.scoring.set(false);}});}
  label(v:string):string{return v.replaceAll('_',' ');}tone(v:string):string{return v.toLowerCase().replaceAll('_','-');}factor(f:Factor):string{return String(f['description']||f['factor']||f['feature']||f['name']||JSON.stringify(f));}policyEntries(v:Record<string,unknown>):[string,unknown][]{return Object.entries(v);}
}
