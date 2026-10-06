import { Component, inject, signal, computed, effect } from '@angular/core';
import { RouterOutlet, RouterLink, Router } from '@angular/router';
import { AuthService } from '../../core/services/auth';
import { LanguageService } from '../../core/services/language';
import { ChaptersService } from '../../core/services/chapters';
import { ApiService } from '../../core/services/api';
import { ReviewQueueService } from '../../core/services/review-queue.service';
import { isAdminEmail, isReviewerEmail } from '../../core/utils/admin';
import { subjectIcon, subjectName } from '../../core/utils/subjects';
import { ChapterSummary, SubtopicGroup, ReviewItem } from '../../core/models/models';

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
  reviewQueue = inject(ReviewQueueService);

  langMenuOpen = signal(false);
  userMenuOpen = signal(false);

  // Super dropdown states: all open by default
  superWithVideoOpen = signal(true);
  superWithoutVideoOpen = signal(true);
  superReviewVideoOpen = signal(true);

  toggleSuper(section: 'with_video' | 'without_video' | 'review_video'): void {
    if (section === 'with_video') {
      this.superWithVideoOpen.update((v) => !v);
    } else if (section === 'review_video') {
      this.superReviewVideoOpen.update((v) => !v);
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
  isReviewer = computed(() => isReviewerEmail(this.auth.user()?.email));

  constructor() {
    effect(() => {
      if (this.isReviewer()) {
        this.reviewQueue.refresh();
      }
    });
  }

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

  // Review videos pending review grouped by subject -> chapter
  reviewSubjectGroups = computed(() => {
    const items = this.reviewQueue.items();
    const map = new Map<string, Map<string, ReviewItem[]>>();
    for (const s of this.defaultSubjects) {
      map.set(s, new Map());
    }
    for (const it of items) {
      const subj = it.subject.toLowerCase();
      if (!map.has(subj)) map.set(subj, new Map());
      const chMap = map.get(subj)!;
      if (!chMap.has(it.chapter)) chMap.set(it.chapter, []);
      chMap.get(it.chapter)!.push(it);
    }
    return Array.from(map.entries())
      .filter(([_, chMap]) => chMap.size > 0)
      .sort((a, b) => a[0].localeCompare(b[0]))
      .map(([subject, chMap]) => ({
        subject,
        chapters: Array.from(chMap.entries())
          .sort((a, b) => a[0].localeCompare(b[0]))
          .map(([chapter, videos]) => ({
            chapter,
            subject,
            class: videos[0]?.class ?? 0,
            video_count: videos.length,
            videos,
          })),
        totalVideos: Array.from(chMap.values()).reduce((sum, vids) => sum + vids.length, 0),
      }));
  });

  totalReviewVideoCount = computed(() =>
    this.reviewSubjectGroups().reduce((acc, g) => acc + g.totalVideos, 0),
  );

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

  isSubjectOpen(section: 'with_video' | 'without_video' | 'review_video', subject: string): boolean {
    return this.expandedSubjects().has(`${section}:${subject}`);
  }

  toggleSubject(section: 'with_video' | 'without_video' | 'review_video', subject: string): void {
    const key = `${section}:${subject}`;
    this.expandedSubjects.update((set) => {
      const next = new Set(set);
      next.has(key) ? next.delete(key) : next.add(key);
      return next;
    });
  }

  private chapterKey(ch: ChapterSummary | { subject: string; chapter: string }): string {
    return `${ch.subject}:${ch.chapter}`;
  }

  isChapterOpen(section: 'with_video' | 'without_video' | 'review_video', ch: ChapterSummary | { subject: string; chapter: string }): boolean {
    return this.expandedChapters().has(`${section}:${this.chapterKey(ch)}`);
  }

  toggleChapter(section: 'with_video' | 'without_video' | 'review_video', ch: ChapterSummary | { subject: string; chapter: string }): void {
    const key = `${section}:${this.chapterKey(ch)}`;
    const baseKey = this.chapterKey(ch);
    const isOpen = this.expandedChapters().has(key);

    this.expandedChapters.update((set) => {
      const next = new Set(set);
      isOpen ? next.delete(key) : next.add(key);
      return next;
    });

    if (section !== 'review_video' && !isOpen && !this.chapterSubtopics()[baseKey]) {
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
