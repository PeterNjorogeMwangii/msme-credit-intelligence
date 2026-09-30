import { Component, EventEmitter, Input, Output } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { LucideAngularModule, LayoutDashboard, Users, FileCheck2, ShieldCheck, TriangleAlert, FileBarChart, Settings } from 'lucide-angular';

interface NavigationItem { label: string; route: string; icon: string; }
const sidebarIcons = { LayoutDashboard, Users, FileCheck2, ShieldCheck, TriangleAlert, FileBarChart, Settings };

@Component({
  selector: 'app-sidebar',
  imports: [RouterLink, RouterLinkActive, LucideAngularModule.pick(sidebarIcons)],
  templateUrl: './sidebar.html',
  styleUrl: './sidebar.scss'
})
export class Sidebar {
  @Input() open = false;
  @Output() navigate = new EventEmitter<void>();
  readonly items: NavigationItem[] = [
    { label: 'Dashboard', route: '/dashboard', icon: 'layout-dashboard' },
    { label: 'Customers', route: '/customers', icon: 'users' },
    { label: 'Credit Assessments', route: '/credit-assessments', icon: 'file-check-2' },
    { label: 'Portfolio Risk', route: '/portfolio-risk', icon: 'shield-check' },
    { label: 'Alerts & Watchlist', route: '/alerts', icon: 'triangle-alert' },
    { label: 'Reports', route: '/reports', icon: 'file-bar-chart' },
    { label: 'Administration', route: '/administration', icon: 'settings' }
  ];
}
