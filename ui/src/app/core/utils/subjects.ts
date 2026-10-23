const SUBJECT_ICON: Record<string, string> = {
  physics: 'fa-atom',
  math: 'fa-square-root-variable',
  chemistry: 'fa-flask',
  biology: 'fa-dna',
};
const SUBJECT_COLOR: Record<string, string> = {
  physics: 'bg-sky-500/10 border-sky-500/30 text-sky-400',
  math: 'bg-amber-500/10 border-amber-500/30 text-amber-400',
  chemistry: 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400',
  biology: 'bg-rose-500/10 border-rose-500/30 text-rose-400',
};
const SUBJECT_NAME: Record<string, string> = {
  physics: 'Physics',
  math: 'Maths',
  chemistry: 'Chemistry',
  biology: 'Biology',
};

export function subjectIcon(subject: string): string {
  return SUBJECT_ICON[subject] ?? 'fa-book';
}

export function subjectName(subject: string): string {
  return SUBJECT_NAME[subject] ?? subject;
}

export function subjectColor(subject: string): string {
  return SUBJECT_COLOR[subject] ?? 'bg-slate-500/10 border-slate-500/30 text-slate-400';
}
