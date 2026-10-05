import { Component, inject, signal, AfterViewInit, NgZone } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { ApiService } from '../../../core/services/api';
import { AuthService } from '../../../core/services/auth';
import { apiErrorMessage } from '../../../core/utils/api-error';

declare const google: any;

// Shared across the sevis.store apps (sevis-web, drive-ui) — same Google Cloud
// project, already allowed server-side in user-service's google.client-ids.
const GOOGLE_CLIENT_ID = '1059813087193-btfkk2bhtj50grqjta6anvo5i7vq77pl.apps.googleusercontent.com';

@Component({
  selector: 'app-login',
  imports: [FormsModule],
  templateUrl: './login.html',
})
export class LoginComponent implements AfterViewInit {
  private api = inject(ApiService);
  private auth = inject(AuthService);
  private router = inject(Router);
  private zone = inject(NgZone);

  email = '';
  password = '';
  loading = signal(false);
  error = signal('');

  ngAfterViewInit(): void {
    const script = document.createElement('script');
    script.src = 'https://accounts.google.com/gsi/client';
    script.async = true;
    script.onload = () => {
      google.accounts.id.initialize({
        client_id: GOOGLE_CLIENT_ID,
        callback: (response: { credential: string }) =>
          this.zone.run(() => this.onGoogleLogin(response.credential)),
      });
      google.accounts.id.renderButton(document.getElementById('google-signin-btn')!, {
        theme: 'filled_black', size: 'large', width: 300, text: 'signin_with',
      });
    };
    document.head.appendChild(script);
  }

  onGoogleLogin(idToken: string): void {
    this.loading.set(true);
    this.error.set('');
    this.api.loginWithGoogle(idToken).subscribe({
      next: (res) => {
        this.auth.setSession(res.token, { name: res.name ?? res.email, email: res.email, role: res.role });
        this.router.navigate(['/']);
      },
      error: (err) => {
        this.error.set(
          err?.status === 404
            ? 'No platform account found for this Google email. Sign up on sevis.store first, then come back here.'
            : apiErrorMessage(err, 'Google sign-in failed. Please try again.'),
        );
        this.loading.set(false);
      },
    });
  }

  onSubmit(): void {
    if (!this.email || !this.password) return;
    this.loading.set(true);
    this.error.set('');

    this.api.login({ email: this.email, password: this.password }).subscribe({
      next: (res) => {
        this.auth.setSession(res.token, { name: res.name, email: res.email, role: res.role });
        this.router.navigate(['/']);
      },
      error: (err) => {
        this.error.set(apiErrorMessage(err, 'Invalid credentials. Please try again.'));
        this.loading.set(false);
      },
    });
  }
}
