import { Component, inject, signal, computed } from '@angular/core';
import { RouterOutlet, RouterLink, Router } from '@angular/router';
import { AuthService } from '../../core/services/auth';
import { LanguageService } from '../../core/services/language';
import { ChaptersService } from '../../core/services/chapters';
import { ApiService } from '../../core/services/api';
import { isAdminEmail } from '../../core/utils/admin';
import { subjectIcon, subjectName } from '../../core/utils/subjects';
import { ChapterSummary, SubtopicGroup } from '../../core/models/models';

@Component({
  selector: 'app-shell',
  imports: [RouterOutlet, RouterLink],
  templateUrl: './shell.html',
})
export class ShellComponent {
  auth = inject(AuthService);
  lang = inject(LanguageService);
  chaptersSvc = inject(ChaptersService);
  private api = inject(ApiService);
  private router = inject(Router);

  langMenuOpen = signal(false);
  userMenuOpen = signal(false);

  currentLanguageName = computed(() => {
    const code = this.lang.current();
    return this.lang.languages().find((l) => l.code === code)?.name ?? code;
  });

  initial = computed(() => (this.auth.user()?.name?.trim()?.[0] ?? '?').toUpperCase());
  isAdmin = computed(() => isAdminEmail(this.auth.user()?.email));

  private expandedSubjects = signal<Set<string>>(new Set());
  private expandedChapters = signal<Set<string>>(new Set());
  private chapterSubtopics = signal<Record<string, SubtopicGroup[] | 'loading'>>({});

  chapters = computed<ChapterSummary[]>(() =>
    [...this.chaptersSvc.chapters()].sort((a, b) => a.class - b.class || a.subject.localeCompare(b.subject) || a.chapter.localeCompare(b.chapter)),
  );

  subjectGroups = computed(() => {
    const bySubject = new Map<string, ChapterSummary[]>();
    for (const ch of this.chapters()) {
      if (!bySubject.has(ch.subject)) bySubject.set(ch.subject, []);
      bySubject.get(ch.subject)!.push(ch);
    }
    return Array.from(bySubject.entries())
      .sort((a, b) => a[0].localeCompare(b[0]))
      .map(([subject, chs]) => ({ subject, chapters: chs }));
  });

  subjectIcon(subject: string): string {
    return subjectIcon(subject);
  }

  subjectName(subject: string): string {
    return subjectName(subject);
  }

  isSubjectOpen(subject: string): boolean {
    return this.expandedSubjects().has(subject);
  }

  toggleSubject(subject: string): void {
    this.expandedSubjects.update((set) => {
      const next = new Set(set);
      next.has(subject) ? next.delete(subject) : next.add(subject);
      return next;
    });
  }

  private chapterKey(ch: ChapterSummary): string {
    return `${ch.class}:${ch.subject}:${ch.chapter}`;
  }

  isChapterOpen(ch: ChapterSummary): boolean {
    return this.expandedChapters().has(this.chapterKey(ch));
  }

  subtopicsFor(ch: ChapterSummary): SubtopicGroup[] | 'loading' | undefined {
    return this.chapterSubtopics()[this.chapterKey(ch)];
  }

  toggleChapter(ch: ChapterSummary): void {
    const key = this.chapterKey(ch);
    const isOpen = this.expandedChapters().has(key);

    this.expandedChapters.update((set) => {
      const next = new Set(set);
      isOpen ? next.delete(key) : next.add(key);
      return next;
    });

    if (!isOpen && !this.chapterSubtopics()[key]) {
      this.chapterSubtopics.update((map) => ({ ...map, [key]: 'loading' }));
      this.api.getSubtopics(ch.subject, String(ch.class), ch.chapter).subscribe({
        next: (detail) => this.chapterSubtopics.update((map) => ({ ...map, [key]: detail.subtopics })),
        error: () => this.chapterSubtopics.update((map) => ({ ...map, [key]: [] })),
      });
    }
  }

  toggleLangMenu(): void {
    this.userMenuOpen.set(false);
    this.langMenuOpen.update((v) => !v);
  }

  toggleUserMenu(): void {
    this.langMenuOpen.set(false);
    this.userMenuOpen.update((v) => !v);
  }

  closeMenus(): void {
    this.langMenuOpen.set(false);
    this.userMenuOpen.set(false);
  }

  selectLanguage(code: string): void {
    this.lang.set(code);
    this.langMenuOpen.set(false);
  }

  search(term: string): void {
    const q = term.trim();
    this.router.navigate(['/'], q ? { queryParams: { q } } : {});
  }

  logout(): void {
    this.auth.clearSession();
  }
}
