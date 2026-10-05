import { Component, inject, signal, computed } from '@angular/core';
import { ApiService } from '../../../core/services/api';
import { AuthService } from '../../../core/services/auth';
import { ReviewItem } from '../../../core/models/models';

const DIFFICULTY_LABELS: Record<string, string> = {
  foundation: 'Foundation',
  jee_main: 'JEE Main',
  jee_advanced_neet: 'JEE Advanced / NEET',
};

const DIFFICULTY_COLOR: Record<string, string> = {
  foundation: 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30',
  jee_main: 'bg-amber-500/10 text-amber-300 border-amber-500/30',
  jee_advanced_neet: 'bg-purple-500/10 text-purple-300 border-purple-500/30',
};

@Component({
  selector: 'app-review-queue',
  imports: [],
  templateUrl: './review-queue.html',
})
export class ReviewQueueComponent {
  private api = inject(ApiService);
  private auth = inject(AuthService);

  items = signal<ReviewItem[]>([]);
  loading = signal(true);
  openComment = signal<string | null>(null);
  commentText = signal('');
  busy = signal<string | null>(null);

  // "To Review": never looked at yet. "Changes Requested": feedback already
  // left, waiting on a regenerate — kept visible in its own tab so it doesn't
  // get lost in (or re-clutter) the main review queue.
  activeTab = signal<'review' | 'feedback'>('review');
  toReview = computed(() => this.items().filter((i) => !i.review_comment));
  needsFixes = computed(() => this.items().filter((i) => !!i.review_comment));
  visibleItems = computed(() => (this.activeTab() === 'review' ? this.toReview() : this.needsFixes()));

  constructor() {
    this.refresh();
  }

  refresh(): void {
    this.loading.set(true);
    this.api.getReviewQueue().subscribe({
      next: (items) => {
        this.items.set(items);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }

  streamUrl(runId: string): string {
    return this.api.streamUrl(runId, this.auth.token());
  }

  difficultyColor(d: string): string {
    return DIFFICULTY_COLOR[d] ?? 'bg-sky-500/10 text-sky-300 border-sky-500/30';
  }

  difficultyLabel(item: ReviewItem): string {
    if (item.content_type === 'explainer') return 'Explainer';
    return DIFFICULTY_LABELS[item.difficulty] ?? item.difficulty;
  }

  approve(runId: string): void {
    this.busy.set(runId);
    this.api.approveRun(runId).subscribe({
      next: () => {
        this.items.update((list) => list.filter((i) => i.run_id !== runId));
        this.busy.set(null);
      },
      error: () => this.busy.set(null),
    });
  }

  toggleComment(runId: string): void {
    this.commentText.set('');
    this.openComment.set(this.openComment() === runId ? null : runId);
  }

  submitComment(runId: string): void {
    const text = this.commentText().trim();
    if (!text) return;
    this.busy.set(runId);
    this.api.commentRun(runId, text).subscribe({
      next: () => {
        this.items.update((list) => list.map((i) => (i.run_id === runId ? { ...i, review_comment: text } : i)));
        this.openComment.set(null);
        this.busy.set(null);
      },
      error: () => this.busy.set(null),
    });
  }
}
