import { Component, inject, input, computed } from '@angular/core';
import { RouterLink } from '@angular/router';
import { ChaptersService } from '../../../core/services/chapters';
import { ChapterSummary } from '../../../core/models/models';
import { subjectIcon, subjectColor } from '../../../core/utils/subjects';

interface ChapterGroup {
  subject: string;
  class: number;
  chapters: ChapterSummary[];
}

@Component({
  selector: 'app-chapter-list',
  imports: [RouterLink],
  templateUrl: './chapter-list.html',
})
export class ChapterListComponent {
  private chaptersSvc = inject(ChaptersService);

  q = input<string>('');

  loading = this.chaptersSvc.loading;

  groups = computed<ChapterGroup[]>(() => {
    const term = (this.q() ?? '').trim().toLowerCase();
    const all = this.chaptersSvc.chapters();
    const filtered = term
      ? all.filter((ch) => ch.chapter.toLowerCase().includes(term) || ch.subject.toLowerCase().includes(term))
      : all;

    const bySubjectClass = new Map<string, ChapterGroup>();
    for (const ch of filtered) {
      const key = `${ch.subject}-${ch.class}`;
      if (!bySubjectClass.has(key)) bySubjectClass.set(key, { subject: ch.subject, class: ch.class, chapters: [] });
      bySubjectClass.get(key)!.chapters.push(ch);
    }
    return Array.from(bySubjectClass.values()).sort((a, b) => a.class - b.class || a.subject.localeCompare(b.subject));
  });

  icon(subject: string): string {
    return subjectIcon(subject);
  }

  color(subject: string): string {
    return subjectColor(subject);
  }
}
