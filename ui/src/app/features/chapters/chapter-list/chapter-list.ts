import { Component, inject, input, computed } from '@angular/core';
import { RouterLink } from '@angular/router';
import { ChaptersService } from '../../../core/services/chapters';
import { ChapterSummary } from '../../../core/models/models';
import { subjectIcon, subjectColor, subjectName } from '../../../core/utils/subjects';

interface ChapterGroup {
  subject: string;
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

    const bySubject = new Map<string, ChapterGroup>();
    for (const ch of filtered) {
      const key = ch.subject;
      if (!bySubject.has(key)) bySubject.set(key, { subject: ch.subject, chapters: [] });
      bySubject.get(key)!.chapters.push(ch);
    }
    return Array.from(bySubject.values()).sort((a, b) => a.subject.localeCompare(b.subject));
  });

  icon(subject: string): string {
    return subjectIcon(subject);
  }

  color(subject: string): string {
    return subjectColor(subject);
  }

  subjectName(subject: string): string {
    return subjectName(subject);
  }
}
