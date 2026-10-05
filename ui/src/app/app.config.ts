import { ApplicationConfig, provideBrowserGlobalErrorListeners, provideZonelessChangeDetection, provideAppInitializer, inject } from '@angular/core';
import { provideRouter, withComponentInputBinding } from '@angular/router';
import { provideHttpClient, withInterceptors, HttpClient } from '@angular/common/http';
import { routes } from './app.routes';
import { authInterceptor } from './core/interceptors/auth-interceptor';

export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    // No zone.js in this project (signals-only). Without explicitly opting into
    // Angular's zoneless scheduler, async updates outside a few framework-tracked
    // paths (e.g. a plain HttpClient .subscribe() callback) update signals but
    // never get flushed to the DOM until some unrelated event forces a tick —
    // e.g. chapter data loading but staying invisible until the next navigation.
    provideZonelessChangeDetection(),
    provideRouter(routes, withComponentInputBinding()),
    provideHttpClient(withInterceptors([authInterceptor])),
    // Forces HttpClient (and anything that depends on it, like ApiService/LanguageService)
    // to be constructed here, in a guaranteed-valid injection context during bootstrap —
    // before the router's initial navigation lazy-loads a route component and tries to
    // construct it from there instead, which was intermittently losing injection context
    // and surfacing as a misleading NG0203 error.
    provideAppInitializer(() => {
      inject(HttpClient);
    }),
  ],
};
