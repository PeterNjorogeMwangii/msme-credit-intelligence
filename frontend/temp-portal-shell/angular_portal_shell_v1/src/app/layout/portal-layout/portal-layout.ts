import { Component, signal } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { Sidebar } from '../sidebar/sidebar';
import { Topbar } from '../topbar/topbar';

@Component({
  selector: 'app-portal-layout',
  imports: [RouterOutlet, Sidebar, Topbar],
  templateUrl: './portal-layout.html',
  styleUrl: './portal-layout.scss'
})
export class PortalLayout {
  readonly sidebarOpen = signal(false);
  toggleSidebar(): void { this.sidebarOpen.update((value) => !value); }
  closeSidebar(): void { this.sidebarOpen.set(false); }
}
