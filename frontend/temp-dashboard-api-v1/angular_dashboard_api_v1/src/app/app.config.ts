import {
  ApplicationConfig,
  importProvidersFrom,
  provideBrowserGlobalErrorListeners,
  provideZonelessChangeDetection
} from '@angular/core';
import { provideHttpClient, withFetch } from '@angular/common/http';
import { provideRouter } from '@angular/router';
import {
  ArrowUpRight, Bell, ChevronDown, FileBarChart, FileCheck2,
  Landmark, LayoutDashboard, LucideAngularModule, Menu, Percent,
  Plus, RefreshCw, Search, Settings, ShieldCheck, TriangleAlert, Users
} from 'lucide-angular';
import { routes } from './app.routes';

export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideZonelessChangeDetection(),
    provideRouter(routes),
    provideHttpClient(withFetch()),
    importProvidersFrom(
      LucideAngularModule.pick({
        ArrowUpRight, Bell, ChevronDown, FileBarChart, FileCheck2,
        Landmark, LayoutDashboard, Menu, Percent, Plus, RefreshCw,
        Search, Settings, ShieldCheck, TriangleAlert, Users
      })
    )
  ]
};
