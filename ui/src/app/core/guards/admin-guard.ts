import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from '../services/auth';
import { isAdminEmail } from '../utils/admin';

export const adminGuard: CanActivateFn = () => {
  const auth = inject(AuthService);
  const router = inject(Router);
  return isAdminEmail(auth.user()?.email) ? true : router.createUrlTree(['/']);
};
