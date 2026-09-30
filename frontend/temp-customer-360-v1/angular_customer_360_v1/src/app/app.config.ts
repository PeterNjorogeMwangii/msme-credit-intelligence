import { ApplicationConfig, importProvidersFrom, provideBrowserGlobalErrorListeners, provideZonelessChangeDetection } from '@angular/core';
import { provideHttpClient, withFetch } from '@angular/common/http';
import { provideRouter } from '@angular/router';
import {
  Activity, ArrowLeft, ArrowRight, ArrowUpRight, BadgeCheck, Bell,
  Building2, ChevronDown, CreditCard, Eye, FileBarChart, FileCheck2,
  FileText, Landmark, LayoutDashboard, LucideAngularModule, Menu,
  Percent, Plus, RefreshCw, Search, Settings, ShieldCheck,
  TrendingUp, TriangleAlert, Users, Wallet
} from 'lucide-angular';
import { routes } from './app.routes';

export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(), provideZonelessChangeDetection(),
    provideRouter(routes), provideHttpClient(withFetch()),
    importProvidersFrom(LucideAngularModule.pick({
      Activity, ArrowLeft, ArrowRight, ArrowUpRight, BadgeCheck, Bell,
      Building2, ChevronDown, CreditCard, Eye, FileBarChart, FileCheck2,
      FileText, Landmark, LayoutDashboard, Menu, Percent, Plus, RefreshCw,
      Search, Settings, ShieldCheck, TrendingUp, TriangleAlert, Users, Wallet
    }))
  ]
};
