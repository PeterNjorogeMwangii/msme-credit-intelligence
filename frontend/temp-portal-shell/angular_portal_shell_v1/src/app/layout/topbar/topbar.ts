import { Component, EventEmitter, Output } from '@angular/core';
import { LucideAngularModule, Menu, Search, Bell, ChevronDown } from 'lucide-angular';
const topbarIcons = { Menu, Search, Bell, ChevronDown };

@Component({ selector: 'app-topbar', imports: [LucideAngularModule.pick(topbarIcons)], templateUrl: './topbar.html', styleUrl: './topbar.scss' })
export class Topbar {
  @Output() menuClick = new EventEmitter<void>();
}
