import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { LucideAngularModule } from 'lucide-angular';
import { finalize } from 'rxjs';
import { AuthService } from '../../../../core/auth/auth.service';

@Component({
  selector: 'app-login-page',
  imports: [FormsModule, LucideAngularModule],
  templateUrl: './login-page.html',
  styleUrl: './login-page.scss',
})
export class LoginPage {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);

  username = 'credit.analyst';
  password = '';
  readonly busy = signal(false);
  readonly error = signal('');
  readonly showPassword = signal(false);

  submit(): void {
    if (!this.username.trim() || !this.password) return;
    this.busy.set(true);
    this.error.set('');
    this.auth
      .login(this.username.trim(), this.password)
      .pipe(finalize(() => this.busy.set(false)))
      .subscribe({
        next: () => {
          const returnUrl = this.route.snapshot.queryParamMap.get('returnUrl') || '/dashboard';
          void this.router.navigateByUrl(returnUrl);
        },
        error: (error: HttpErrorResponse) => {
          this.error.set(error.error?.detail || 'Unable to sign in. Please try again.');
        },
      });
  }
}
