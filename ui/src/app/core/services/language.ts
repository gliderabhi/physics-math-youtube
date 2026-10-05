import { Injectable, inject, signal } from '@angular/core';
import { ApiService } from './api';
import { LanguageOption } from '../models/models';

const STORAGE_KEY = 'physics_yt_lang';

@Injectable({ providedIn: 'root' })
export class LanguageService {
  private api = inject(ApiService);

  private _languages = signal<LanguageOption[]>([]);
  private _current = signal<string>(localStorage.getItem(STORAGE_KEY) || 'en');

  readonly languages = this._languages.asReadonly();
  readonly current = this._current.asReadonly();

  constructor() {
    this.api.getLanguages().subscribe((langs) => {
      this._languages.set(langs);
      if (langs.length && !langs.some((l) => l.code === this._current())) {
        this.set(langs[0].code);
      }
    });
  }

  set(code: string): void {
    localStorage.setItem(STORAGE_KEY, code);
    this._current.set(code);
  }
}
