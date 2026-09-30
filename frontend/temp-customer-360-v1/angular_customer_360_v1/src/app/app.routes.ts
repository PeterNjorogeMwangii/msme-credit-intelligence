import { Routes } from '@angular/router';
import { PortalLayout } from './layout/portal-layout/portal-layout';
import { DashboardPage } from './features/dashboard/pages/dashboard-page/dashboard-page';
import { CustomerListPage } from './features/customers/pages/customer-list-page/customer-list-page';
import { Customer360Page } from './features/customers/pages/customer-360-page/customer-360-page';

export const routes: Routes = [
  {
    path: '', component: PortalLayout,
    children: [
      { path: 'dashboard', component: DashboardPage, title: 'Dashboard | MSME Credit Intelligence' },
      { path: 'customers', component: CustomerListPage, title: 'Customers | MSME Credit Intelligence' },
      { path: 'customers/:customerId', component: Customer360Page, title: 'Customer 360 | MSME Credit Intelligence' },
      { path: '', pathMatch: 'full', redirectTo: 'dashboard' }
    ]
  },
  { path: '**', redirectTo: 'dashboard' }
];
