import { ApplicationConfig, importProvidersFrom, provideBrowserGlobalErrorListeners, provideZonelessChangeDetection } from '@angular/core';
import { provideHttpClient, withFetch } from '@angular/common/http';
import { provideRouter } from '@angular/router';
import {
  Activity, ArrowLeft, ArrowRight, ArrowUpRight, BadgeCheck, Bell, Building2,
  Check, CheckCircle2, ChevronDown, CreditCard, Eye, FileBarChart, FileCheck2,
  FileText, Gauge, Info, Landmark, LayoutDashboard, LucideAngularModule,
  Menu, Percent, Play, Plus, RefreshCw, Search, Settings, ShieldCheck,
  TrendingUp, TriangleAlert, UserPlus, Users, Wallet, X, XCircle
} from 'lucide-angular';
import { routes } from './app.routes';

export const appConfig:ApplicationConfig={providers:[provideBrowserGlobalErrorListeners(),provideZonelessChangeDetection(),provideRouter(routes),provideHttpClient(withFetch()),importProvidersFrom(LucideAngularModule.pick({Activity,ArrowLeft,ArrowRight,ArrowUpRight,BadgeCheck,Bell,Building2,Check,CheckCircle2,ChevronDown,CreditCard,Eye,FileBarChart,FileCheck2,FileText,Gauge,Info,Landmark,LayoutDashboard,Menu,Percent,Play,Plus,RefreshCw,Search,Settings,ShieldCheck,TrendingUp,TriangleAlert,UserPlus,Users,Wallet,X,XCircle}))]};
