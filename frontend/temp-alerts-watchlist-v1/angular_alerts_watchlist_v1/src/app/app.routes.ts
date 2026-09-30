import { Routes } from '@angular/router';
import { PortalLayout } from './layout/portal-layout/portal-layout';
import { DashboardPage } from './features/dashboard/pages/dashboard-page/dashboard-page';
import { CustomerListPage } from './features/customers/pages/customer-list-page/customer-list-page';
import { Customer360Page } from './features/customers/pages/customer-360-page/customer-360-page';
import { AssessmentListPage } from './features/credit-assessments/pages/assessment-list-page/assessment-list-page';
import { AssessmentDetailPage } from './features/credit-assessments/pages/assessment-detail-page/assessment-detail-page';
import { PortfolioRiskPage } from './features/portfolio-risk/pages/portfolio-risk-page/portfolio-risk-page';
import { AlertsPage } from './features/alerts/pages/alerts-page/alerts-page';

export const routes:Routes=[{path:'',component:PortalLayout,children:[
  {path:'dashboard',component:DashboardPage,title:'Dashboard | MSME Credit Intelligence'},
  {path:'customers',component:CustomerListPage,title:'Customers | MSME Credit Intelligence'},
  {path:'customers/:customerId',component:Customer360Page,title:'Customer 360 | MSME Credit Intelligence'},
  {path:'credit-assessments',component:AssessmentListPage,title:'Credit Assessments | MSME Credit Intelligence'},
  {path:'credit-assessments/:applicationId',component:AssessmentDetailPage,title:'Assessment Detail | MSME Credit Intelligence'},
  {path:'portfolio-risk',component:PortfolioRiskPage,title:'Portfolio Risk | MSME Credit Intelligence'},
  {path:'alerts',component:AlertsPage,title:'Alerts & Watchlist | MSME Credit Intelligence'},
  {path:'',pathMatch:'full',redirectTo:'dashboard'}
]},{path:'**',redirectTo:'dashboard'}];
