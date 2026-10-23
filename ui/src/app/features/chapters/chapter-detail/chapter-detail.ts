import { Component, inject, input, signal, effect, computed } from '@angular/core';
import { RouterLink } from '@angular/router';
import { ApiService } from '../../../core/services/api';
import { AuthService } from '../../../core/services/auth';
import { LanguageService } from '../../../core/services/language';
import { isAdminEmail } from '../../../core/utils/admin';
import { ChapterDetail, SubtopicItem } from '../../../core/models/models';

const DIFFICULTY_LABELS: Record<string, string> = {
  foundation: 'Foundation',
  jee_main: 'JEE Main',
  jee_advanced_neet: 'JEE Advanced / NEET',
};

const DIFFICULTY_ICON: Record<string, string> = {
  explainer: 'fa-book-open',
  foundation: 'fa-bullseye',
  jee_main: 'fa-rocket',
  jee_advanced_neet: 'fa-trophy',
};

const DIFFICULTY_COLOR: Record<string, string> = {
  foundation: 'bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-300 border-emerald-500/30',
  jee_main: 'bg-amber-500/10 hover:bg-amber-500/20 text-amber-300 border-amber-500/30',
  jee_advanced_neet: 'bg-purple-500/10 hover:bg-purple-500/20 text-purple-300 border-purple-500/30',
};

@Component({
  selector: 'app-chapter-detail',
  imports: [RouterLink],
  templateUrl: './chapter-detail.html',
})
export class ChapterDetailComponent {
  private api = inject(ApiService);
  private auth = inject(AuthService);
  lang = inject(LanguageService);

  subject = input.required<string>();
  class_ = input.required<string>({ alias: 'class' });
  chapter = input.required<string>();

  detail = signal<ChapterDetail | null>(null);
  loading = signal(true);
  generatingKeys = signal<Set<string>>(new Set());

  isAdmin = computed(() => isAdminEmail(this.auth.user()?.email));

  visibleSubtopics = computed(() => {
    const d = this.detail();
    if (!d) return [];
    return d.subtopics.map((group) => {
      const explainer = group.items.find((i) => i.content_type === 'explainer') ?? null;
      let problems = group.problems ?? [];
      if (!problems.length) {
        const legacyProblems = group.items.filter((i) => i.content_type === 'problem' && (this.isAdmin() || this.isAvailable(i)));
        problems = legacyProblems.map((lp, idx) => ({
          problem_index: idx + 1,
          title: lp.title ?? `Problem ${idx + 1}`,
          status: this.isAvailable(lp) ? 'available' : 'pending',
          run_id: lp.run_ids[this.lang.current()] ?? null,
        }));
      }
      return {
        subtopic: group.subtopic,
        explainer,
        problems,
      };
    });
  });

  constructor() {
    effect(() => {
      this.loading.set(true);
      this.api.getSubtopics(this.subject(), this.class_(), this.chapter()).subscribe({
        next: (d) => {
          this.detail.set(d);
          this.loading.set(false);
        },
        error: () => this.loading.set(false),
      });
    });
  }

  difficultyLabel(d: string | null): string {
    return d ? (DIFFICULTY_LABELS[d] ?? d) : 'Explainer';
  }

  difficultyIcon(d: string | null): string {
    return DIFFICULTY_ICON[d ?? 'explainer'] ?? 'fa-book';
  }

  difficultyColor(d: string | null): string {
    return DIFFICULTY_COLOR[d ?? ''] ?? 'bg-sky-500/10 hover:bg-sky-500/20 text-sky-300 border-sky-500/30';
  }

  trackItem(item: SubtopicItem): string {
    return item.content_type + item.difficulty;
  }

  // Null means no run for the current language — template falls back to the placeholder.
  explainerThumbnail(item: SubtopicItem): string | null {
    const runId = item.run_ids[this.lang.current()];
    return runId ? this.api.thumbnailUrl(runId, this.auth.token()) : null;
  }

  isAvailable(item: SubtopicItem): boolean {
    return item.exists && item.languages.includes(this.lang.current());
  }

  private key(item: SubtopicItem, subtopic: string): string {
    return `${subtopic}::${item.content_type}::${item.difficulty ?? ''}`;
  }

  isGenerating(item: SubtopicItem, subtopic: string): boolean {
    return this.generatingKeys().has(this.key(item, subtopic));
  }

  generate(item: SubtopicItem, subtopic: string): void {
    const key = this.key(item, subtopic);
    if (this.generatingKeys().has(key)) return;
    this.generatingKeys.update((set) => new Set(set).add(key));
    this.api
      .generateVideo(this.subject(), Number(this.class_()), this.chapter(), subtopic, item.content_type, item.difficulty ?? '', this.lang.current())
      .subscribe();
  }
}
