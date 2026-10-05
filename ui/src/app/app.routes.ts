import { Routes } from '@angular/router';
import { authGuard, loggedInGuard } from './core/guards/auth-guard';
import { adminGuard } from './core/guards/admin-guard';

export const routes: Routes = [
  {
    path: 'login',
    canActivate: [loggedInGuard],
    loadComponent: () => import('./features/auth/login/login').then((m) => m.LoginComponent),
  },
  {
    path: '',
    canActivate: [authGuard],
    loadComponent: () => import('./features/shell/shell').then((m) => m.ShellComponent),
    children: [
      { path: '', loadComponent: () => import('./features/chapters/chapter-list/chapter-list').then((m) => m.ChapterListComponent) },
      { path: 'chapter', loadComponent: () => import('./features/chapters/chapter-detail/chapter-detail').then((m) => m.ChapterDetailComponent) },
      { path: 'player', loadComponent: () => import('./features/player/player').then((m) => m.PlayerComponent) },
      {
        path: 'admin/review',
        canActivate: [adminGuard],
        loadComponent: () => import('./features/admin/review-queue/review-queue').then((m) => m.ReviewQueueComponent),
      },
    ],
  },
  { path: '**', redirectTo: '' },
];
