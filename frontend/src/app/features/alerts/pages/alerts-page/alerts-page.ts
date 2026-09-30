import { Component, OnInit, inject, signal } from '@angular/core';
import { DatePipe, DecimalPipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { LucideAngularModule } from 'lucide-angular';
import { AlertItem, AlertSummary } from '../../models/alert.model';
import { AlertService } from '../../services/alert.service';

@Component({selector:'app-alerts-page',imports:[DatePipe,DecimalPipe,FormsModule,RouterLink,LucideAngularModule],templateUrl:'./alerts-page.html',styleUrl:'./alerts-page.scss'})
export class AlertsPage implements OnInit{
  private readonly service=inject(AlertService);readonly records=signal<AlertItem[]>([]);readonly summary=signal<AlertSummary|null>(null);readonly selected=signal<AlertItem|null>(null);readonly loading=signal(true);readonly actionLoading=signal(false);readonly error=signal<string|null>(null);readonly message=signal<string|null>(null);readonly total=signal(0);readonly pages=signal(0);
  page=1;pageSize=20;search='';status='';severity='';alertType='';unassigned=false;assignedTo='';resolutionNotes='';resolution:'RESOLVED'|'DISMISSED'='RESOLVED';
  ngOnInit():void{this.load();}load():void{this.loading.set(true);this.error.set(null);this.service.load({page:this.page,pageSize:this.pageSize,search:this.search,status:this.status,severity:this.severity,alertType:this.alertType,unassigned:this.unassigned}).subscribe({next:r=>{this.summary.set(r.summary);this.records.set(r.list.records);this.total.set(r.list.total_records);this.pages.set(r.list.total_pages);this.loading.set(false);},error:e=>{console.error(e);this.error.set('Risk alerts could not be retrieved from FastAPI.');this.loading.set(false);}});}
  apply():void{this.page=1;this.load();}clear():void{this.search='';this.status='';this.severity='';this.alertType='';this.unassigned=false;this.page=1;this.load();}previous():void{if(this.page>1){this.page--;this.load();}}next():void{if(this.page<this.pages()){this.page++;this.load();}}
  open(item:AlertItem):void{this.message.set(null);this.resolutionNotes='';this.assignedTo=item.assigned_to||'';this.service.detail(item.alert_id).subscribe({next:value=>this.selected.set(value),error:e=>{console.error(e);this.message.set('Alert details could not be loaded.');}});}close():void{this.selected.set(null);this.message.set(null);}
  acknowledge():void{const item=this.selected();if(!item)return;this.run(this.service.acknowledge(item.alert_id,this.assignedTo||null),'Alert acknowledged.');}assign():void{const item=this.selected();if(!item||!this.assignedTo.trim()){this.message.set('Enter a valid security user UUID before assigning.');return;}this.run(this.service.assign(item.alert_id,this.assignedTo.trim()),'Alert assigned and moved under investigation.');}
  finish():void{const item=this.selected();if(!item||this.resolutionNotes.trim().length<3){this.message.set('Enter resolution notes of at least three characters.');return;}this.run(this.service.resolve(item.alert_id,this.resolutionNotes.trim(),this.resolution),`Alert ${this.resolution.toLowerCase()}.`);}
  private run(request:ReturnType<AlertService['acknowledge']>,message:string):void{this.actionLoading.set(true);this.message.set(null);request.subscribe({next:value=>{this.selected.set(value);this.message.set(message);this.actionLoading.set(false);this.load();},error:e=>{console.error(e);this.message.set(e.error?.detail||'The alert action could not be completed.');this.actionLoading.set(false);}});}
  label(value:string):string{return value.replaceAll('_',' ');}tone(value?:string):string{return(value||'unknown').toLowerCase().replaceAll('_','-');}
}
