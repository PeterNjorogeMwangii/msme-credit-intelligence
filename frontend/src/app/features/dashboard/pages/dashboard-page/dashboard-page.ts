import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { CurrencyPipe, DatePipe, DecimalPipe, PercentPipe } from '@angular/common';
import { RouterLink } from '@angular/router';
import { LucideAngularModule } from 'lucide-angular';
import { DashboardData } from '../../models/dashboard.model';
import { DashboardService } from '../../services/dashboard.service';

@Component({
  selector: 'app-dashboard-page',
  imports: [CurrencyPipe, DatePipe, DecimalPipe, PercentPipe, RouterLink, LucideAngularModule],
  templateUrl: './dashboard-page.html',
  styleUrl: './dashboard-page.scss'
})
export class DashboardPage implements OnInit {
  private readonly dashboardService = inject(DashboardService);
  readonly data = signal<DashboardData | null>(null);
  readonly loading = signal(true);
  readonly error = signal<string | null>(null);
  readonly riskBands = computed(() => this.data()?.portfolio.risk_bands ?? []);

  ngOnInit(): void { this.load(); }

  load(): void {
    this.loading.set(true);
    this.error.set(null);
    this.dashboardService.loadDashboard().subscribe({
      next: (response) => { this.data.set(response); this.loading.set(false); },
      error: (error) => {
        console.error('Dashboard API error', error);
        this.error.set('The dashboard could not retrieve data from FastAPI. Confirm that the backend and Angular proxy are running.');
        this.loading.set(false);
      }
    });
  }

  riskLabel(value: string): string { return value.replaceAll('_', ' '); }
  riskClass(value: string): string { return value.toLowerCase().replaceAll('_', '-'); }
}
