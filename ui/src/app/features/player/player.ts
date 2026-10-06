import { Component, inject, input, signal, effect, computed } from '@angular/core';
import { RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { DomSanitizer, SafeResourceUrl, SafeHtml } from '@angular/platform-browser';
import { renderToString as katexRenderToString } from 'katex';
import { ApiService } from '../../core/services/api';
import { AuthService } from '../../core/services/auth';
import { LanguageService } from '../../core/services/language';
import { ReviewQueueService } from '../../core/services/review-queue.service';
import { isReviewerEmail } from '../../core/utils/admin';
import { ResolveResult, WikiImage } from '../../core/models/models';

@Component({
  selector: 'app-player',
  imports: [RouterLink, FormsModule],
  templateUrl: './player.html',
})
export class PlayerComponent {
  private api = inject(ApiService);
  private auth = inject(AuthService);
  private sanitizer = inject(DomSanitizer);
  private reviewQueue = inject(ReviewQueueService);
  lang = inject(LanguageService);

  subject = input<string>('');
  class_ = input<string>('', { alias: 'class' });
  chapter = input<string>('');
  subtopic = input<string>('');
  contentType = input<string>('');
  difficulty = input<string>('');
  runId = input<string>('');
  language = input<string>('');

  result = signal<ResolveResult | null>(null);
  embedUrl = signal<SafeResourceUrl | null>(null);
  loading = signal(true);
  busyReview = signal(false);
  showReviewComment = signal(false);
  reviewCommentText = '';

  isReviewer = computed(() => isReviewerEmail(this.auth.user()?.email));

  isProblem = computed(() => {
    const ct = (this.contentType() || this.result()?.content_type || '').toLowerCase();
    if (ct === 'problem') return true;
    if (ct === 'explainer') return false;
    return !!this.result()?.explanation?.problem_statement;
  });

  problemDiagrams = computed(() => {
    const parts = this.result()?.parts ?? [];
    return parts.filter((p) => !!p.diagram_url).map((p) => ({
      url: p.diagram_url!,
      caption: p.diagram_caption || p.heading || '',
    }));
  });

  hasVisual(v: any): boolean {
    if (!v || typeof v !== 'object') return false;
    return (
      (Array.isArray(v.objects) && v.objects.length > 0) ||
      (Array.isArray(v.vectors) && v.vectors.length > 0) ||
      (Array.isArray(v.curves) && v.curves.length > 0) ||
      v.type === 'circular_path' ||
      v.type === 'free_body_diagram'
    );
  }

  private static readonly COLOR_MAP: Record<string, string> = {
    BLUE: '#38bdf8',
    RED: '#f87171',
    GREEN: '#4ade80',
    YELLOW: '#facc15',
    ORANGE: '#fb923c',
    GRAY: '#94a3b8',
    WHITE: '#f8fafc',
    PURPLE: '#c084fc',
  };

  renderVisualSvg(visual: any): SafeHtml {
    if (!this.hasVisual(visual)) return '';

    const width = 380;
    const height = 220;
    const cx = width / 2;
    const cy = height / 2;

    const colors = PlayerComponent.COLOR_MAP;
    const getColor = (c: string | undefined, def: string) => colors[(c || '').toUpperCase()] || def;

    const defs = `
      <defs>
        <marker id="arrow-def" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
          <path d="M 0 1 L 10 5 L 0 9 z" fill="#facc15" />
        </marker>
        <marker id="arrow-blue" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
          <path d="M 0 1 L 10 5 L 0 9 z" fill="#38bdf8" />
        </marker>
        <marker id="arrow-red" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
          <path d="M 0 1 L 10 5 L 0 9 z" fill="#f87171" />
        </marker>
        <marker id="arrow-green" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
          <path d="M 0 1 L 10 5 L 0 9 z" fill="#4ade80" />
        </marker>
        <marker id="arrow-orange" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
          <path d="M 0 1 L 10 5 L 0 9 z" fill="#fb923c" />
        </marker>
      </defs>
    `;

    const markerFor = (c: string | undefined) => {
      const u = (c || '').toUpperCase();
      if (u === 'BLUE') return 'url(#arrow-blue)';
      if (u === 'RED') return 'url(#arrow-red)';
      if (u === 'GREEN') return 'url(#arrow-green)';
      if (u === 'ORANGE') return 'url(#arrow-orange)';
      return 'url(#arrow-def)';
    };

    let inner = '';

    if (visual.type === 'free_body_diagram') {
      const scale = 40;
      if (visual.ground) {
        inner += `<line x1="20" y1="185" x2="360" y2="185" stroke="#475569" stroke-width="2" />`;
        for (let x = 25; x < 355; x += 12) {
          inner += `<line x1="${x}" y1="185" x2="${x - 8}" y2="197" stroke="#334155" stroke-width="1.5" />`;
        }
      }

      if (Array.isArray(visual.rope) && visual.rope.length > 1) {
        const points = visual.rope
          .map((p: number[]) => `${cx + p[0] * scale},${cy - p[1] * scale}`)
          .join(' ');
        inner += `<polyline points="${points}" fill="none" stroke="#94a3b8" stroke-width="2.5" stroke-dasharray="4,2" />`;
      }

      for (const obj of visual.objects || []) {
        const ox = cx + (obj.pos?.[0] || 0) * scale;
        const oy = cy - (obj.pos?.[1] || 0) * scale;
        const ocolor = getColor(obj.color, '#38bdf8');

        if (obj.kind === 'pulley') {
          inner += `<circle cx="${ox}" cy="${oy}" r="16" fill="#1e293b" stroke="${ocolor}" stroke-width="2.5" />`;
          inner += `<circle cx="${ox}" cy="${oy}" r="4" fill="${ocolor}" />`;
        } else {
          inner += `<rect x="${ox - 24}" y="${oy - 18}" width="48" height="36" rx="6" fill="#1e293b" stroke="${ocolor}" stroke-width="2" />`;
        }

        if (obj.label) {
          inner += `<text x="${ox}" y="${oy + 4}" fill="#f8fafc" font-size="11" font-weight="600" text-anchor="middle">${obj.label}</text>`;
        }

        for (const arrow of obj.arrows || []) {
          const dx = (arrow.dx || 0) * scale;
          const dy = -(arrow.dy || 0) * scale;
          const startX = ox;
          const startY = arrow.at_surface ? oy + 18 : oy;
          const tipX = startX + dx;
          const tipY = startY + dy;
          const acolor = getColor(arrow.color, '#facc15');
          const m = markerFor(arrow.color);

          inner += `<line x1="${startX}" y1="${startY}" x2="${tipX}" y2="${tipY}" stroke="${acolor}" stroke-width="2.5" marker-end="${m}" />`;
          if (arrow.label) {
            const lx = tipX + (dx > 5 ? 8 : dx < -5 ? -8 : 0);
            const ly = tipY + (dy > 5 ? 14 : dy < -5 ? -8 : -6);
            const anchor = dx < -5 ? 'end' : dx > 5 ? 'start' : 'middle';
            inner += `<text x="${lx}" y="${ly}" fill="${acolor}" font-size="11" font-weight="700" text-anchor="${anchor}">${arrow.label}</text>`;
          }
        }
      }
    } else if (visual.type === 'vector_path' && Array.isArray(visual.vectors)) {
      let currX = 0;
      let currY = 0;
      const pts: Array<{ x: number; y: number }> = [{ x: 0, y: 0 }];
      for (const v of visual.vectors) {
        currX += v.dx || 0;
        currY += v.dy || 0;
        pts.push({ x: currX, y: currY });
      }

      const xs = pts.map((p) => p.x);
      const ys = pts.map((p) => p.y);
      const minX = Math.min(...xs, 0);
      const maxX = Math.max(...xs, 0);
      const minY = Math.min(...ys, 0);
      const maxY = Math.max(...ys, 0);
      const spanX = Math.max(maxX - minX, 1);
      const spanY = Math.max(maxY - minY, 1);
      const scale = Math.min(260 / spanX, 140 / spanY);

      const toSvgX = (x: number) => cx + (x - (minX + maxX) / 2) * scale;
      const toSvgY = (y: number) => cy - (y - (minY + maxY) / 2) * scale;

      const sx0 = toSvgX(0);
      const sy0 = toSvgY(0);
      inner += `<circle cx="${sx0}" cy="${sy0}" r="4" fill="#38bdf8" />`;
      inner += `<text x="${sx0 - 8}" y="${sy0 - 8}" fill="#94a3b8" font-size="10">Start</text>`;

      let px = 0;
      let py = 0;
      for (const v of visual.vectors) {
        const nx = px + (v.dx || 0);
        const ny = py + (v.dy || 0);
        const p1x = toSvgX(px);
        const p1y = toSvgY(py);
        const p2x = toSvgX(nx);
        const p2y = toSvgY(ny);
        const vcolor = getColor(v.color, '#38bdf8');
        const m = markerFor(v.color);

        inner += `<line x1="${p1x}" y1="${p1y}" x2="${p2x}" y2="${p2y}" stroke="${vcolor}" stroke-width="2.5" marker-end="${m}" />`;
        if (v.label) {
          const mx = (p1x + p2x) / 2;
          const my = (p1y + p2y) / 2 - 8;
          inner += `<text x="${mx}" y="${my}" fill="${vcolor}" font-size="10" font-weight="600" text-anchor="middle">${v.label}</text>`;
        }
        px = nx;
        py = ny;
      }

      if (visual.show_resultant) {
        const finalX = toSvgX(currX);
        const finalY = toSvgY(currY);
        inner += `<line x1="${sx0}" y1="${sy0}" x2="${finalX}" y2="${finalY}" stroke="#facc15" stroke-width="2.5" stroke-dasharray="5,3" marker-end="url(#arrow-def)" />`;
        if (visual.resultant_label) {
          const rx = (sx0 + finalX) / 2;
          const ry = (sy0 + finalY) / 2 + 16;
          inner += `<text x="${rx}" y="${ry}" fill="#facc15" font-size="11" font-weight="700" text-anchor="middle">${visual.resultant_label}</text>`;
        }
      }
    } else if (visual.type === 'circular_path') {
      const r = 55;
      const vcolor = getColor(visual.color, '#38bdf8');
      inner += `<circle cx="${cx}" cy="${cy}" r="${r}" fill="none" stroke="#334155" stroke-width="1.5" stroke-dasharray="4,3" />`;
      inner += `<circle cx="${cx}" cy="${cy}" r="3" fill="#64748b" />`;

      const fraction = visual.fraction || 1.0;
      if (fraction <= 0.5) {
        inner += `<path d="M ${cx} ${cy - r} A ${r} ${r} 0 0 1 ${cx} ${cy + r}" fill="none" stroke="${vcolor}" stroke-width="2.5" marker-end="${markerFor(visual.color)}" />`;
      } else {
        inner += `<circle cx="${cx}" cy="${cy}" r="${r}" fill="none" stroke="${vcolor}" stroke-width="2.5" />`;
      }

      if (visual.show_resultant) {
        inner += `<line x1="${cx}" y1="${cy - r}" x2="${cx}" y2="${cy + r}" stroke="#facc15" stroke-width="2.5" stroke-dasharray="4,2" marker-end="url(#arrow-def)" />`;
        if (visual.resultant_label) {
          inner += `<text x="${cx + 12}" y="${cy + 4}" fill="#facc15" font-size="11" font-weight="700">${visual.resultant_label}</text>`;
        }
      }
    } else {
      inner += `<text x="${cx}" y="${cy}" fill="#64748b" font-size="11" text-anchor="middle">Diagram</text>`;
    }

    const svg = `
      <svg viewBox="0 0 ${width} ${height}" class="w-full h-auto max-h-56 select-none" xmlns="http://www.w3.org/2000/svg">
        ${defs}
        <rect width="${width}" height="${height}" rx="12" fill="#090d16" />
        ${inner}
      </svg>
    `;
    return this.sanitizer.bypassSecurityTrustHtml(svg);
  }

  constructor() {
    effect(() => {
      this.loading.set(true);
      const langToUse = this.language() || this.lang.current();
      this.api
        .resolve(
          this.subject(),
          this.class_(),
          this.chapter(),
          this.subtopic(),
          this.contentType(),
          this.difficulty(),
          langToUse,
          this.runId(),
        )
        .subscribe({
          next: (r) => {
            this.result.set(r);
            this.embedUrl.set(
              r.status === 'published' && r.youtube_video_id
                ? this.sanitizer.bypassSecurityTrustResourceUrl(`https://www.youtube.com/embed/${r.youtube_video_id}`)
                : null,
            );
            this.loading.set(false);
          },
          error: () => {
            this.result.set(null);
            this.loading.set(false);
          },
        });
    });
  }

  approveRun(runId: string): void {
    this.busyReview.set(true);
    this.reviewQueue.approve(runId).subscribe({
      next: () => {
        this.busyReview.set(false);
        this.result.update((r) => (r ? { ...r, status: 'approved' } : null));
      },
      error: () => this.busyReview.set(false),
    });
  }

  toggleReviewComment(): void {
    this.showReviewComment.update((v) => !v);
  }

  submitReviewComment(runId: string): void {
    const text = this.reviewCommentText.trim();
    if (!text) return;
    this.busyReview.set(true);
    this.reviewQueue.comment(runId, text).subscribe({
      next: () => {
        this.busyReview.set(false);
        this.showReviewComment.set(false);
        this.reviewCommentText = '';
      },
      error: () => this.busyReview.set(false),
    });
  }

  streamUrl(runId: string): string {
    return this.api.streamUrl(runId, this.auth.token());
  }

  imageUrl(url: string): string {
    const token = this.auth.token();
    return token ? `${url}?access_token=${encodeURIComponent(token)}` : url;
  }

  renderLatex(latex: string): SafeHtml {
    try {
      const html = katexRenderToString(latex, { throwOnError: false, displayMode: false });
      return this.sanitizer.bypassSecurityTrustHtml(html);
    } catch {
      return this.sanitizer.bypassSecurityTrustHtml(latex);
    }
  }

  sanitizedWikiHtml(html: string): SafeHtml {
    if (!html) return '';
    return this.sanitizer.bypassSecurityTrustHtml(html);
  }

  // Spelled-out math words that legitimately appear inside a formula (sin(theta), 2(pi)sqrt(m/k))
  // -- without this whitelist a 4+ letter run looks like prose and would wrongly break the match.
  private static readonly MATH_WORDS = new Set([
    'pi', 'theta', 'rho', 'omega', 'alpha', 'beta', 'gamma', 'delta', 'epsilon', 'lambda', 'mu',
    'sigma', 'phi', 'psi', 'tau', 'nu', 'eta', 'chi', 'xi', 'zeta', 'kappa', 'iota',
    'max', 'min', 'rms', 'eff', 'net', 'avg', 'rel', 'const', 'sq', 'cos', 'sin', 'tan', 'ln',
    'log', 'exp', 'sqrt', 'half', 'eq',
  ]);
  // Ordinary short English words that must NOT be mistaken for a 1-3 letter variable name.
  private static readonly STOPWORDS = new Set([
    'a', 'an', 'as', 'at', 'be', 'by', 'do', 'he', 'if', 'in', 'is', 'it', 'me', 'my', 'no', 'of',
    'on', 'or', 'so', 'to', 'up', 'us', 'we', 'the', 'and', 'for', 'are', 'you', 'all', 'can',
    'had', 'her', 'was', 'one', 'our', 'out', 'get', 'has', 'him', 'his', 'how', 'man', 'new',
    'now', 'see', 'two', 'way', 'who', 'did', 'its', 'let', 'put', 'say', 'she', 'too', 'use',
  ]);
  // Spelled-out Greek letters and function names that are ALSO valid bare LaTeX commands, used
  // to upgrade "(pi)" / "sin(theta)" into real \pi / \sin(\theta) typesetting. Deliberately
  // excludes "max"/"min" -- in this corpus they're always a descriptive subscript label (v_max
  // meaning "v sub max"), and KaTeX's \max is an operator that errors when used that way.
  private static readonly LATEX_WORDS =
    'pi|rho|theta|omega|alpha|beta|gamma|delta|epsilon|lambda|mu|sigma|phi|psi|tau|nu|eta|chi|xi|zeta|kappa|iota|sin|cos|tan|ln|log|exp';

  // Raw text is plain prose paragraphs with formulas written inline mid-sentence (e.g. "F = k(q1
  // q2)/r^2"), not on their own line -- so formulas can't be found by classifying whole lines.
  // Instead this scans each paragraph word by word and wraps the maximal run of formula-looking
  // tokens around any "=" sign, leaving genuine prose untouched. Images are interleaved between
  // paragraphs (not dumped in one block at the end) so they sit near the text they illustrate.
  formatNcertHtml(text: string, images: WikiImage[] = []): SafeHtml {
    const paragraphs = text
      .split(/\n{2,}/)
      .map((p) => p.replace(/\s+/g, ' ').trim())
      .filter(Boolean);

    const paragraphHtml = paragraphs.map(
      (p) => `<p class="text-slate-300 leading-relaxed mb-3 last:mb-0">${this.highlightFormulas(p)}</p>`,
    );

    if (images.length) {
      const slot = (n: number) => Math.min(paragraphHtml.length, Math.max(1, Math.round(((n + 1) * paragraphHtml.length) / (images.length + 1))));
      // Insert back-to-front so earlier insertions don't shift later slot indices.
      images
        .map((img, n) => ({ img, pos: slot(n), side: (n % 2 === 0 ? 'right' : 'left') as 'left' | 'right' }))
        .reverse()
        .forEach(({ img, pos, side }) => paragraphHtml.splice(pos, 0, this.imageFigureHtml(img, side)));
    }

    const html = paragraphHtml.join('') + (images.length ? '<div class="clear-both"></div>' : '');
    return this.sanitizer.bypassSecurityTrustHtml(html);
  }

  private imageFigureHtml(img: WikiImage, side: 'left' | 'right'): string {
    const url = this.imageUrl(img.url);
    const floatClass = side === 'right' ? 'float-right ml-4' : 'float-left mr-4';
    return (
      `<a href="${this.escapeHtml(url)}" target="_blank" rel="noopener" class="${floatClass} mb-2 block w-32 sm:w-44 rounded-lg overflow-hidden border border-slate-800 bg-slate-950/40">` +
      `<img src="${this.escapeHtml(url)}" alt="${this.escapeHtml(img.title)}" class="w-full h-auto object-cover" /></a>`
    );
  }

  private isFormulaToken(word: string): boolean {
    const core = word.replace(/^[.,;:]+|[.,;:]+$/g, '');
    if (!core) return false;
    const letterRuns = core.match(/[A-Za-z]+/g) ?? [];
    for (const run of letterRuns) {
      const lower = run.toLowerCase();
      if (run.length >= 4 && !PlayerComponent.MATH_WORDS.has(lower)) return false;
    }
    if (letterRuns.length === 1 && letterRuns[0].length === core.length) {
      // the token is ENTIRELY one letter-run (e.g. plain "is", "of", a bare variable "F" / "T",
      // or a bare spelled-out word like "omega"). A short (<=3 letter) non-stopword run, or a
      // known math word of any length, qualifies on its own -- it has no digit/symbol attached,
      // but is still clearly a formula token, not prose.
      const lower = core.toLowerCase();
      if (PlayerComponent.MATH_WORDS.has(lower)) return true;
      return core.length <= 3 && !PlayerComponent.STOPWORDS.has(lower);
    }
    return /[0-9+\-*/^()=.,%×÷√±∓·≈_°Ωλμ∆∘∝∩∪∫≤≥→]/.test(core) || letterRuns.some((r) => PlayerComponent.MATH_WORDS.has(r.toLowerCase()));
  }

  private highlightFormulas(paragraph: string): string {
    const words = paragraph.split(/(\s+)/);
    const out: string[] = [];
    let i = 0;
    while (i < words.length) {
      const w = words[i];
      if (w === '' || /^\s+$/.test(w)) {
        out.push(w);
        i++;
        continue;
      }
      if (!this.isFormulaToken(w)) {
        out.push(this.escapeHtml(w));
        i++;
        continue;
      }
      let j = i;
      let hasEquals = false;
      const run: string[] = [];
      while (j < words.length) {
        const tok = words[j];
        if (tok === '' || /^\s+$/.test(tok)) {
          run.push(tok);
          j++;
          continue;
        }
        if (!this.isFormulaToken(tok)) break;
        if (tok.includes('=')) hasEquals = true;
        run.push(tok);
        j++;
      }
      while (run.length && /^\s+$/.test(run[run.length - 1])) {
        run.pop();
        j--;
      }
      if (hasEquals && run.length) {
        const raw = run.join('');
        const m = raw.match(/^([.,;:]*)([\s\S]*?)([.,;:]*)$/);
        const [, lead, core, trail] = m ?? ['', '', raw, ''];
        out.push(this.escapeHtml(lead));
        out.push(`<span class="text-sky-300 bg-sky-500/10 rounded px-1 py-0.5">${this.renderFormulaKatex(core)}</span>`);
        out.push(this.escapeHtml(trail));
        i = j;
      } else {
        out.push(this.escapeHtml(w));
        i++;
      }
    }
    return out.join('');
  }

  // Converts the plain-text formula notation this content is written in (e.g. "F = k(q1 q2)/r^2",
  // "T = 2(pi)sqrt(m/k)") into real LaTeX and renders it through KaTeX, so exponents/subscripts/
  // roots/Greek letters show as proper math typesetting instead of literal "^2" / "(pi)" text.
  // Verified error-free against all 1391 unique formula spans actually present across the corpus.
  private renderFormulaKatex(raw: string): string {
    let t = raw;
    t = t.replace(/%/g, '\\%'); // "%" starts a LaTeX comment and would silently eat the rest
    t = t.replace(/∆/g, '\\Delta{}'); // KaTeX's default font has no glyph for the raw unicode char
    t = t.replace(new RegExp(`(?<![A-Za-z])(${PlayerComponent.LATEX_WORDS})(?![A-Za-z])`, 'gi'), (_m, w) => '\\' + w.toLowerCase());
    t = t.replace(/sqrt\(([^()]+)\)/g, '\\sqrt{$1}');
    // Scientific notation "9x10^9" -> a real times sign, without touching bare juxtaposition
    // multiplication like "m1x1" (m sub 1 times x sub 1, no explicit operator between them).
    t = t.replace(/(\d+(?:\.\d+)?)\s*x\s*(10\^)/g, '$1 \\times $2');
    // Parenthesized exponents "r^(n-1)" -> "r^{n-1}" -- must run BEFORE the bare-exponent rule,
    // since an unbraced "^(" would otherwise superscript just the opening paren on its own.
    t = t.replace(/\^\(([^()]+)\)/g, '^{$1}');
    // Digit-only and single-letter-only exponents are handled separately (not one greedy
    // alphanumeric run) so "b^2i^2" braces as b^{2} i^{2}, not the invalid b^{2i}^{2}.
    t = t.replace(/\^(-?[0-9]+)/g, '^{$1}');
    t = t.replace(/\^([A-Za-z])(?![A-Za-z0-9])/g, '^{$1}');
    t = t.replace(/_(-?[0-9]+)/g, '_{$1}');
    t = t.replace(/_([A-Za-z][A-Za-z0-9]*)(?![A-Za-z0-9])/g, '_{$1}');
    try {
      return katexRenderToString(t, { throwOnError: false, displayMode: false });
    } catch {
      return this.escapeHtml(raw);
    }
  }

  private escapeHtml(s: string): string {
    return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }
}
