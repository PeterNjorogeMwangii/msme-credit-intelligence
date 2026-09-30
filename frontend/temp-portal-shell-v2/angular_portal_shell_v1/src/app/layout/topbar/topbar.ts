import { Component, EventEmitter, Output } from '@angular/core';
import { LucideAngularModule } from 'lucide-angular';

@Component({ selector: 'app-topbar', imports: [LucideAngularModule], templateUrl: './topbar.html', styleUrl: './topbar.scss' })
export class Topbar {
  @Output() menuClick = new EventEmitter<void>();
}
