import { Component, EventEmitter, Output, computed, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { LucideAngularModule } from 'lucide-angular';
import { AuthService } from '../../core/auth/auth.service';

@Component({ selector: 'app-topbar', imports: [RouterLink, LucideAngularModule], templateUrl: './topbar.html', styleUrl: './topbar.scss' })
export class Topbar {
  @Output() menuClick = new EventEmitter<void>();
  readonly auth = inject(AuthService);
  readonly initials = computed(() => this.auth.user()?.full_name.split(/\s+/).slice(0, 2).map((part) => part[0]).join('').toUpperCase() || 'U');
  readonly roleLabel = computed(() => (this.auth.user()?.role_code || '').replaceAll('_', ' ').toLowerCase().replace(/\b\w/g, (letter) => letter.toUpperCase()));
}
