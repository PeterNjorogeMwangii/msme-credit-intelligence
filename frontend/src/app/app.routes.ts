import { Routes } from '@angular/router';
import { authGuard, administrationGuard } from './core/auth/auth.guard';
import { AlertsPage } from './features/alerts/pages/alerts-page/alerts-page';
import { LoginPage } from './features/auth/pages/login-page/login-page';
import { AssessmentDetailPage } from './features/credit-assessments/pages/assessment-detail-page/assessment-detail-page';
import { AssessmentListPage } from './features/credit-assessments/pages/assessment-list-page/assessment-list-page';
import { Customer360Page } from './features/customers/pages/customer-360-page/customer-360-page';
import { CustomerListPage } from './features/customers/pages/customer-list-page/customer-list-page';
import { DashboardPage } from './features/dashboard/pages/dashboard-page/dashboard-page';
import { AdministrationPage } from './features/administration/pages/administration-page/administration-page';
import { PortfolioRiskPage } from './features/portfolio-risk/pages/portfolio-risk-page/portfolio-risk-page';
import { ReportsPage } from './features/reports/pages/reports-page/reports-page';
import { TransactionAnalyticsPage } from './features/transactions/pages/transaction-analytics-page/transaction-analytics-page';
import { PortalLayout } from './layout/portal-layout/portal-layout';

export const routes: Routes = [
  { path: 'login', component: LoginPage, title: 'Sign in | MSME Credit Intelligence' },
  { path: '', component: PortalLayout, canActivate: [authGuard], children: [
    { path: 'dashboard', component: DashboardPage },
    { path: 'customers', component: CustomerListPage },
    { path: 'customers/:customerId', component: Customer360Page },
    { path: 'credit-assessments', component: AssessmentListPage },
    { path: 'credit-assessments/:applicationId', component: AssessmentDetailPage },
    { path: 'transactions', component: TransactionAnalyticsPage, title:'Transaction Analytics | MSME Credit Intelligence' },
    { path: 'portfolio-risk', component: PortfolioRiskPage },
    { path: 'alerts', component: AlertsPage },
    { path: 'reports', component: ReportsPage },
    { path: 'administration', component: AdministrationPage, canActivate: [administrationGuard], title: 'Administration | MSME Credit Intelligence' },
    { path: '', pathMatch: 'full', redirectTo: 'dashboard' },
  ]},
  { path: '**', redirectTo: 'dashboard' },
];
