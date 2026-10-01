import { ApplicationConfig, importProvidersFrom, provideBrowserGlobalErrorListeners, provideZonelessChangeDetection } from '@angular/core';
import { provideHttpClient, withFetch, withInterceptors } from '@angular/common/http';
import { provideRouter } from '@angular/router';
import { apiUrlInterceptor } from './core/http/api-url.interceptor';
import { Activity, ArrowLeft, ArrowRight, ArrowUpRight, BadgeCheck, Bell, Building2, Check, CheckCircle2, ChevronDown, CreditCard, Download, Eye, EyeOff, FileBarChart, FileCheck2, FileText, Gauge, Info, Landmark, LayoutDashboard, Lock, LogOut, LucideAngularModule, Menu, Percent, Play, Plus, RefreshCw, Search, Settings, ShieldCheck, TrendingUp, TriangleAlert, User, UserCog, UserPlus, Users, Wallet, X, XCircle } from 'lucide-angular';
import { routes } from './app.routes';
import { authInterceptor } from './core/auth/auth.interceptor';

export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideZonelessChangeDetection(),
    provideRouter(routes),
    provideHttpClient(withFetch(), withInterceptors([apiUrlInterceptor, authInterceptor])),
    importProvidersFrom(LucideAngularModule.pick({ Activity, ArrowLeft, ArrowRight, ArrowUpRight, BadgeCheck, Bell, Building2, Check, CheckCircle2, ChevronDown, CreditCard, Download, Eye, EyeOff, FileBarChart, FileCheck2, FileText, Gauge, Info, Landmark, LayoutDashboard, Lock, LogOut, Menu, Percent, Play, Plus, RefreshCw, Search, Settings, ShieldCheck, TrendingUp, TriangleAlert, User, UserCog, UserPlus, Users, Wallet, X, XCircle })),
  ],
};
