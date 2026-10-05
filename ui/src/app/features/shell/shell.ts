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

  // Super dropdown states: both open by default
  superWithVideoOpen = signal(true);
  superWithoutVideoOpen = signal(true);

  toggleSuper(section: 'with_video' | 'without_video'): void {
    if (section === 'with_video') {
      this.superWithVideoOpen.update((v) => !v);
    } else {
      this.superWithoutVideoOpen.update((v) => !v);
    }
  }

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
    [...this.chaptersSvc.chapters()].sort((a, b) => a.subject.localeCompare(b.subject) || a.chapter.localeCompare(b.chapter)),
  );

  private readonly defaultSubjects = ['physics', 'math'];

  // Chapters with video grouped by subject
  videoSubjectGroups = computed(() => {
    const all = this.chapters();
    const map = new Map<string, ChapterSummary[]>();
    for (const s of this.defaultSubjects) {
      map.set(s, []);
    }
    for (const ch of all) {
      if (ch.has_video || (ch.video_count ?? 0) > 0 || (ch.video_subtopics?.length ?? 0) > 0) {
        if (!map.has(ch.subject)) map.set(ch.subject, []);
        map.get(ch.subject)!.push(ch);
      }
    }
    return Array.from(map.entries())
      .sort((a, b) => a[0].localeCompare(b[0]))
      .map(([subject, chs]) => ({
        subject,
        chapters: chs,
        totalVideos: chs.reduce((sum, c) => sum + (c.video_count ?? c.video_subtopics?.length ?? 0), 0),
      }));
  });

  // Chapters without video grouped by subject
  nonVideoSubjectGroups = computed(() => {
    const all = this.chapters();
    const map = new Map<string, ChapterSummary[]>();
    for (const s of this.defaultSubjects) {
      map.set(s, []);
    }
    for (const ch of all) {
      const videoCnt = ch.video_count ?? ch.video_subtopics?.length ?? 0;
      const nonVideoCnt = (ch.subtopic_count || ch.subtopics?.length || 0) - videoCnt;
      if (nonVideoCnt > 0) {
        if (!map.has(ch.subject)) map.set(ch.subject, []);
        map.get(ch.subject)!.push(ch);
      }
    }
    return Array.from(map.entries())
      .sort((a, b) => a[0].localeCompare(b[0]))
      .map(([subject, chs]) => ({
        subject,
        chapters: chs,
        totalTopics: chs.reduce(
          (sum, c) =>
            sum +
            Math.max(
              0,
              (c.subtopic_count || c.subtopics?.length || 0) - (c.video_count ?? c.video_subtopics?.length ?? 0),
            ),
          0,
        ),
      }));
  });

  totalWithVideoCount = computed(() =>
    this.videoSubjectGroups().reduce((acc, g) => acc + g.totalVideos, 0),
  );

  totalWithoutVideoCount = computed(() =>
    this.nonVideoSubjectGroups().reduce((acc, g) => acc + g.totalTopics, 0),
  );

  subjectIcon(subject: string): string {
    return subjectIcon(subject);
  }

  subjectName(subject: string): string {
    return subjectName(subject);
  }

  isSubjectOpen(section: 'with_video' | 'without_video', subject: string): boolean {
    return this.expandedSubjects().has(`${section}:${subject}`);
  }

  toggleSubject(section: 'with_video' | 'without_video', subject: string): void {
    const key = `${section}:${subject}`;
    this.expandedSubjects.update((set) => {
      const next = new Set(set);
      next.has(key) ? next.delete(key) : next.add(key);
      return next;
    });
  }

  private chapterKey(ch: ChapterSummary): string {
    return `${ch.subject}:${ch.chapter}`;
  }

  isChapterOpen(section: 'with_video' | 'without_video', ch: ChapterSummary): boolean {
    return this.expandedChapters().has(`${section}:${this.chapterKey(ch)}`);
  }

  toggleChapter(section: 'with_video' | 'without_video', ch: ChapterSummary): void {
    const key = `${section}:${this.chapterKey(ch)}`;
    const baseKey = this.chapterKey(ch);
    const isOpen = this.expandedChapters().has(key);

    this.expandedChapters.update((set) => {
      const next = new Set(set);
      isOpen ? next.delete(key) : next.add(key);
      return next;
    });

    if (!isOpen && !this.chapterSubtopics()[baseKey]) {
      this.chapterSubtopics.update((map) => ({ ...map, [baseKey]: 'loading' }));
      this.api.getSubtopics(ch.subject, ch.chapter).subscribe({
        next: (detail) => this.chapterSubtopics.update((map) => ({ ...map, [baseKey]: detail.subtopics })),
        error: () => this.chapterSubtopics.update((map) => ({ ...map, [baseKey]: [] })),
      });
    }
  }

  subtopicsFor(section: 'with_video' | 'without_video', ch: ChapterSummary): string[] | 'loading' {
    const baseKey = this.chapterKey(ch);
    const loaded = this.chapterSubtopics()[baseKey];

    if (Array.isArray(loaded)) {
      if (section === 'with_video') {
        const videoList = loaded.filter((st) => st.has_video || ch.video_subtopics?.includes(st.subtopic));
        return videoList.map((st) => st.subtopic);
      } else {
        const nonVideoList = loaded.filter((st) => !st.has_video && !ch.video_subtopics?.includes(st.subtopic));
        return nonVideoList.map((st) => st.subtopic);
      }
    }

    if (loaded === 'loading') {
      return 'loading';
    }

    if (section === 'with_video') {
      return ch.video_subtopics ?? [];
    } else {
      const vSet = new Set(ch.video_subtopics ?? []);
      return (ch.subtopics ?? []).filter((s: string) => !vSet.has(s));
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
