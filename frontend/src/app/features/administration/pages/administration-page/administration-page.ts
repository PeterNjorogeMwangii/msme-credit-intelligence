import { Component, OnInit, inject, signal } from '@angular/core';
import { DatePipe, JsonPipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { LucideAngularModule } from 'lucide-angular';
import { AdminSummary, AuditItem, UserItem } from '../../models/administration.model';
import { AdministrationService } from '../../services/administration.service';

type Tab = 'users' | 'audit';

@Component({
  selector: 'app-administration-page',
  imports: [DatePipe, JsonPipe, FormsModule, LucideAngularModule],
  templateUrl: './administration-page.html',
  styleUrl: './administration-page.scss',
})
export class AdministrationPage implements OnInit {
  private readonly service = inject(AdministrationService);
  readonly summary = signal<AdminSummary | null>(null);
  readonly users = signal<UserItem[]>([]);
  readonly audits = signal<AuditItem[]>([]);
  readonly selectedUser = signal<UserItem | null>(null);
  readonly selectedAudit = signal<AuditItem | null>(null);
  readonly loading = signal(true);
  readonly saving = signal(false);
  readonly error = signal<string | null>(null);
  readonly message = signal<string | null>(null);
  readonly tab = signal<Tab>('users');

  userPage = 1;
  auditPage = 1;
  userPages = 0;
  auditPages = 0;
  userTotal = 0;
  auditTotal = 0;
  userSearch = '';
  auditSearch = '';
  role = '';
  status = '';
  editRole = '';
  editStatus = '';
  reason = '';

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.loading.set(true);
    this.service.load(this.userPage, this.auditPage, this.userSearch, this.role, this.status, this.auditSearch).subscribe({
      next: (r) => {
        this.summary.set(r.summary);
        this.users.set(r.users.records);
        this.audits.set(r.audits.records);
        this.userPages = r.users.total_pages;
        this.auditPages = r.audits.total_pages;
        this.userTotal = r.users.total_records;
        this.auditTotal = r.audits.total_records;
        this.loading.set(false);
      },
      error: (e) => {
        console.error(e);
        this.error.set('Administration data could not be retrieved.');
        this.loading.set(false);
      },
    });
  }

  selectTab(t: Tab): void {
    this.tab.set(t);
  }

  applyUsers(): void {
    this.userPage = 1;
    this.load();
  }

  applyAudits(): void {
    this.auditPage = 1;
    this.load();
  }

  edit(user: UserItem): void {
    this.selectedUser.set(user);
    this.editRole = user.role_code;
    this.editStatus = user.account_status;
    this.reason = '';
    this.message.set(null);
  }

  save(): void {
    const u = this.selectedUser();
    if (!u) return;

    this.saving.set(true);
    this.service.updateUser(u.user_id, this.editRole, this.editStatus, this.reason).subscribe({
      next: (value) => {
        this.selectedUser.set(value);
        this.message.set('User access updated and audit event recorded.');
        this.saving.set(false);
        this.load();
      },
      error: (e) => {
        this.message.set(e.error?.detail || 'User update failed.');
        this.saving.set(false);
      },
    });
  }

  close(): void {
    this.selectedUser.set(null);
    this.selectedAudit.set(null);
    this.message.set(null);
  }

  label(v: string): string {
    return v.replaceAll('_', ' ');
  }

  tone(v: string): string {
    return v.toLowerCase().replaceAll('_', '-');
  }

  userPrev(): void {
    if (this.userPage > 1) {
      this.userPage--;
      this.load();
    }
  }

  userNext(): void {
    if (this.userPage < this.userPages) {
      this.userPage++;
      this.load();
    }
  }

  auditPrev(): void {
    if (this.auditPage > 1) {
      this.auditPage--;
      this.load();
    }
  }

  auditNext(): void {
    if (this.auditPage < this.auditPages) {
      this.auditPage++;
      this.load();
    }
  }
}
