import { HttpErrorResponse } from '@angular/common/http';

export function apiErrorMessage(err: unknown, fallback: string): string {
  if (err instanceof HttpErrorResponse) {
    const body = err.error;
    if (typeof body === 'string' && body.trim()) return body;
    if (body?.error) return body.error;
    if (body?.message) return body.message;
  }
  return fallback;
}
