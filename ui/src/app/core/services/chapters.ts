import { Injectable, inject, signal } from '@angular/core';
import { ApiService } from './api';
import { ChapterSummary } from '../models/models';

/** Single root-level fetch of the full chapter list, shared by the shell's sidebar
 * and the chapter-list grid so both don't each fire their own /api/chapters call. */
@Injectable({ providedIn: 'root' })
export class ChaptersService {
  private api = inject(ApiService);

  private _chapters = signal<ChapterSummary[]>([]);
  private _loading = signal(true);
  readonly chapters = this._chapters.asReadonly();
  readonly loading = this._loading.asReadonly();

  constructor() {
    this.api.getChapters().subscribe({
      next: (chapters) => {
        this._chapters.set(chapters);
        this._loading.set(false);
      },
      error: () => this._loading.set(false),
    });
  }
}
