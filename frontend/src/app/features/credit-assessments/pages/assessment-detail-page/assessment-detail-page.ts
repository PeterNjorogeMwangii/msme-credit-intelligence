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
  label(v:string):string{return v.replaceAll('_',' ');}tone(v:string):string{return v.toLowerCase().replaceAll('_','-');}
  factorLabel(f:Factor):string{if(typeof f==='string')return f;return this.label(String(f['code']||f['factor']||f['feature']||f['name']||'Model factor'));}
  factorValue(f:Factor):string{if(typeof f==='string')return '';const value=f['value'];if(value===null||value===undefined)return '';const code=String(f['code']||'');const n=Number(value);if(code.includes('COVERAGE')&&Number.isFinite(n))return `${n.toFixed(2)}× coverage`;if(code.includes('CASH_FLOW')&&Number.isFinite(n))return new Intl.NumberFormat('en-KE',{style:'currency',currency:'KES',maximumFractionDigits:0}).format(n);if(code.includes('PAST_DUE')&&Number.isFinite(n))return `${n} days`;if(Number.isFinite(n))return n.toLocaleString('en-KE');return String(value);}
  policyEntries(v:Record<string,unknown>):[string,unknown][]{return Object.entries(v).filter(([key])=>key!=='rules');}
  policyRules(v:Record<string,unknown>):Record<string,unknown>[]{const rules=v['rules'];return Array.isArray(rules)?rules.filter(rule=>rule&&typeof rule==='object') as Record<string,unknown>[]:[];}
  policyValue(key:string,value:unknown):string{if(typeof value==='boolean')return value?'Passed':'Failed';if(key.includes('threshold')&&typeof value==='number')return `${(value*100).toFixed(1)}%`;if(value&&typeof value==='object')return JSON.stringify(value);return String(value??'—');}
  ruleTitle(rule:Record<string,unknown>):string{return this.label(String(rule['code']||rule['rule']||rule['name']||rule['policy']||'Policy rule'));}
  rulePassed(rule:Record<string,unknown>):boolean|null{const value=rule['passed']??rule['pass']??rule['result'];if(typeof value==='boolean')return value;if(typeof value==='string'){if(['PASS','PASSED','TRUE'].includes(value.toUpperCase()))return true;if(['FAIL','FAILED','FALSE'].includes(value.toUpperCase()))return false;}return null;}
  ruleDetail(rule:Record<string,unknown>):string{const detail=rule['description']||rule['message']||rule['reason'];if(detail)return String(detail);return Object.entries(rule).filter(([k])=>!['code','rule','name','policy','passed','pass','result'].includes(k)).map(([k,v])=>`${this.label(k)}: ${String(v)}`).join(' · ');}
  isDecline(a:AssessmentDetail):boolean{return a.system_recommendation==='RECOMMEND_DECLINE';}
}
