import { Component } from '@angular/core';
import { LucideAngularModule } from 'lucide-angular';

@Component({ selector: 'app-dashboard-page', imports: [LucideAngularModule], templateUrl: './dashboard-page.html', styleUrl: './dashboard-page.scss' })
export class DashboardPage {
  readonly stats = [
    { label:'Customers', value:'5,000', icon:'users', tone:'blue', note:'Active MSME profiles' },
    { label:'Loans', value:'3,126', icon:'landmark', tone:'green', note:'Across all portfolios' },
    { label:'Default rate', value:'11.89%', icon:'percent', tone:'red', note:'Historical training set' },
    { label:'Risk alerts', value:'287', icon:'triangle-alert', tone:'amber', note:'Require monitoring' }
  ];
  readonly customers = [
    ['C000287','Enterprise 00287 Limited','Transport','CRITICAL','142'],
    ['C002687','Enterprise 02687 Limited','Retail','CRITICAL','92'],
    ['C001407','Enterprise 01407 Limited','Services','HIGH','108']
  ];
}
