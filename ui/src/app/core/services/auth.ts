import { Injectable, signal, computed, inject } from '@angular/core';
import { Router } from '@angular/router';

export interface StoredUser { name: string; email: string; role: string; }

/** A corrupted localStorage value must never throw during a service field
 * initializer — that happens inside Angular's DI context, and an uncaught
 * exception there cascades into misleading NG0203 errors for unrelated
 * services built afterward, blanking the whole app. */
function safeParseUser(raw: string | null): StoredUser | null {
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    localStorage.removeItem('physics_yt_user');
    return null;
  }
}

@Injectable({ providedIn: 'root' })
export class AuthService {
  private router = inject(Router);

  private _token = signal<string | null>(localStorage.getItem('physics_yt_token'));
  private _user = signal<StoredUser | null>(safeParseUser(localStorage.getItem('physics_yt_user')));

  readonly token = this._token.asReadonly();
  readonly user = this._user.asReadonly();
  readonly isLoggedIn = computed(() => !!this._token());

  setSession(token: string, user: StoredUser): void {
    localStorage.setItem('physics_yt_token', token);
    localStorage.setItem('physics_yt_user', JSON.stringify(user));
    this._token.set(token);
    this._user.set(user);
  }

  clearSession(): void {
    localStorage.removeItem('physics_yt_token');
    localStorage.removeItem('physics_yt_user');
    this._token.set(null);
    this._user.set(null);
    this.router.navigate(['/login']);
  }
}
