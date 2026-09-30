import { Component, EventEmitter, Input, Output, inject } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { LucideAngularModule } from 'lucide-angular';
import { AuthService } from '../../core/auth/auth.service';

interface NavigationItem { label:string; route:string; icon:string; roles?:string[]; }
@Component({selector:'app-sidebar',imports:[RouterLink,RouterLinkActive,LucideAngularModule],templateUrl:'./sidebar.html',styleUrl:'./sidebar.scss'})
export class Sidebar {
  @Input() open=false; @Output() navigate=new EventEmitter<void>(); readonly auth=inject(AuthService);
  readonly items:NavigationItem[]=[
    {label:'Dashboard',route:'/dashboard',icon:'layout-dashboard'},
    {label:'Customers',route:'/customers',icon:'users'},
    {label:'Credit Assessments',route:'/credit-assessments',icon:'file-check-2'},
    {label:'Transactions',route:'/transactions',icon:'activity'},
    {label:'Portfolio Risk',route:'/portfolio-risk',icon:'shield-check'},
    {label:'Alerts & Watchlist',route:'/alerts',icon:'triangle-alert'},
    {label:'Reports',route:'/reports',icon:'file-bar-chart'},
    {label:'Administration',route:'/administration',icon:'settings',roles:['RISK_MANAGER','SYSTEM_ADMIN']}
  ];
  visible(item:NavigationItem){return !item.roles||this.auth.hasAnyRole(...item.roles);}
}
