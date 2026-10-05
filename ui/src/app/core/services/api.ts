import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import {
  LoginRequest, AuthResponse, LanguageOption,
  ChapterSummary, ChapterDetail, ResolveResult, ReviewItem,
} from '../models/models';

const BASE = '';

@Injectable({ providedIn: 'root' })
export class ApiService {
  constructor(private http: HttpClient) {}

  // ── Auth (shared user-service, same login used across the sevis platform) ──
  login(body: LoginRequest): Observable<AuthResponse> {
    return this.http.post<AuthResponse>(`${BASE}/user-service/api/auth/login`, body);
  }

  loginWithGoogle(idToken: string): Observable<AuthResponse> {
    return this.http.post<AuthResponse>(`${BASE}/user-service/api/auth/google`, { idToken });
  }

  // ── Curriculum / content ─────────────────────────────────────────────────
  getLanguages(): Observable<LanguageOption[]> {
    return this.http.get<LanguageOption[]>(`${BASE}/physics-service/api/languages`);
  }

  getChapters(): Observable<ChapterSummary[]> {
    return this.http.get<ChapterSummary[]>(`${BASE}/physics-service/api/chapters`);
  }

  getSubtopics(subject: string, arg2: string, arg3?: string): Observable<ChapterDetail> {
    let classValue: string | undefined;
    let chapter: string;
    if (arg3 !== undefined) {
      classValue = arg2;
      chapter = arg3;
    } else {
      chapter = arg2;
    }
    let params = new HttpParams().set('subject', subject).set('chapter', chapter);
    if (classValue) {
      params = params.set('class', classValue);
    }
    return this.http.get<ChapterDetail>(`${BASE}/physics-service/api/subtopics`, { params });
  }

  resolve(
    subject: string,
    classValue: string,
    chapter: string,
    subtopic: string,
    contentType: string,
    difficulty: string,
    language: string,
  ): Observable<ResolveResult> {
    let params = new HttpParams()
      .set('subject', subject)
      .set('chapter', chapter)
      .set('subtopic', subtopic)
      .set('content_type', contentType)
      .set('difficulty', difficulty)
      .set('language', language);
    if (classValue) {
      params = params.set('class', classValue);
    }
    return this.http.get<ResolveResult>(`${BASE}/physics-service/api/resolve`, { params });
  }

  streamUrl(runId: string, token: string | null): string {
    return `${BASE}/physics-service/api/stream/${runId}${token ? '?access_token=' + encodeURIComponent(token) : ''}`;
  }

  thumbnailUrl(runId: string, token: string | null): string {
    return `${BASE}/physics-service/api/thumbnail/${runId}${token ? '?access_token=' + encodeURIComponent(token) : ''}`;
  }

  // ── Admin review queue ───────────────────────────────────────────────────
  getReviewQueue(): Observable<ReviewItem[]> {
    return this.http.get<ReviewItem[]>(`${BASE}/physics-service/api/admin/review-queue`);
  }

  approveRun(runId: string): Observable<unknown> {
    return this.http.post(`${BASE}/physics-service/api/admin/review/${runId}/approve`, {});
  }

  commentRun(runId: string, comment: string): Observable<unknown> {
    return this.http.post(`${BASE}/physics-service/api/admin/review/${runId}/comment`, { comment });
  }

  generateVideo(
    subject: string,
    classValue: number,
    chapter: string,
    subtopic: string,
    contentType: string,
    difficulty: string,
    language: string,
  ): Observable<unknown> {
    return this.http.post(`${BASE}/physics-service/api/admin/generate`, {
      subject,
      class: classValue,
      chapter,
      subtopic,
      content_type: contentType,
      difficulty,
      language,
    });
  }
}
