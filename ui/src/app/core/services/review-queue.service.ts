import { Injectable, inject, signal } from '@angular/core';
import { Observable, tap } from 'rxjs';
import { ApiService } from './api';
import { AuthService } from './auth';
import { ReviewItem } from '../models/models';
import { isReviewerEmail } from '../utils/admin';

@Injectable({ providedIn: 'root' })
export class ReviewQueueService {
  private api = inject(ApiService);
  private auth = inject(AuthService);

  private _items = signal<ReviewItem[]>([]);
  private _loading = signal(false);
  readonly items = this._items.asReadonly();
  readonly loading = this._loading.asReadonly();

  refresh(): void {
    if (!isReviewerEmail(this.auth.user()?.email)) {
      this._items.set([]);
      return;
    }
    this._loading.set(true);
    this.api.getReviewQueue().subscribe({
      next: (items) => {
        this._items.set(items);
        this._loading.set(false);
      },
      error: () => this._loading.set(false),
    });
  }

  approve(runId: string): Observable<unknown> {
    return this.api.approveRun(runId).pipe(
      tap(() => {
        this._items.update((list) => list.filter((i) => i.run_id !== runId));
      }),
    );
  }

  comment(runId: string, comment: string): Observable<unknown> {
    return this.api.commentRun(runId, comment).pipe(
      tap(() => {
        this._items.update((list) =>
          list.map((i) => (i.run_id === runId ? { ...i, review_comment: comment } : i)),
        );
      }),
    );
  }
}
