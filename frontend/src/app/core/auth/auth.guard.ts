import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from './auth.service';

export const authGuard: CanActivateFn = (_, state) => {
  const auth = inject(AuthService);
  if (auth.authenticated()) return true;
  return inject(Router).createUrlTree(['/login'], {
    queryParams: { returnUrl: state.url },
  });
};

export const administrationGuard: CanActivateFn = () => {
  const auth = inject(AuthService);
  return auth.hasAnyRole('RISK_MANAGER', 'SYSTEM_ADMIN')
    ? true
    : inject(Router).createUrlTree(['/dashboard']);
};
