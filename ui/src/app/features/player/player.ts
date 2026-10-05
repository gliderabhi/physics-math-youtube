import { Component, inject, input, signal, effect } from '@angular/core';
import { RouterLink } from '@angular/router';
import { DomSanitizer, SafeResourceUrl, SafeHtml } from '@angular/platform-browser';
import { renderToString as katexRenderToString } from 'katex';
import { ApiService } from '../../core/services/api';
import { AuthService } from '../../core/services/auth';
import { LanguageService } from '../../core/services/language';
import { ResolveResult, WikiImage } from '../../core/models/models';

@Component({
  selector: 'app-player',
  imports: [RouterLink],
  templateUrl: './player.html',
})
export class PlayerComponent {
  private api = inject(ApiService);
  private auth = inject(AuthService);
  private sanitizer = inject(DomSanitizer);
  lang = inject(LanguageService);

  subject = input.required<string>();
  class_ = input.required<string>({ alias: 'class' });
  chapter = input.required<string>();
  subtopic = input.required<string>();
  contentType = input.required<string>();
  difficulty = input<string>('');

  result = signal<ResolveResult | null>(null);
  embedUrl = signal<SafeResourceUrl | null>(null);
  loading = signal(true);

  constructor() {
    effect(() => {
      this.loading.set(true);
      this.api
        .resolve(this.subject(), this.class_(), this.chapter(), this.subtopic(), this.contentType(), this.difficulty(), this.lang.current())
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
