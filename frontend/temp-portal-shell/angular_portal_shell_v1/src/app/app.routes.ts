import { Routes } from '@angular/router';
import { PortalLayout } from './layout/portal-layout/portal-layout';
import { DashboardPage } from './features/dashboard/pages/dashboard-page/dashboard-page';

export const routes: Routes = [
  {
    path: '',
    component: PortalLayout,
    children: [
      { path: 'dashboard', component: DashboardPage, title: 'Dashboard | MSME Credit Intelligence' },
      { path: '', pathMatch: 'full', redirectTo: 'dashboard' }
    ]
  },
  { path: '**', redirectTo: 'dashboard' }
];
