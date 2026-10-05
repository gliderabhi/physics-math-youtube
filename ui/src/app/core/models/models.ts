export interface LoginRequest {
  email: string;
  password: string;
}

export interface AuthResponse {
  token: string;
  userId: number;
  name: string;
  email: string;
  role: string;
  accountType: string;
}

export interface LanguageOption {
  code: string;
  name: string;
}

export interface ChapterSummary {
  subject: string;
  class: number;
  chapter: string;
  subtopic_count: number;
  subtopics?: string[];
  has_video?: boolean;
  video_count?: number;
  video_subtopics?: string[];
}

export interface SubtopicItem {
  content_type: string;
  difficulty: string | null;
  exists: boolean;
  title: string | null;
  languages: string[];
  run_ids: Record<string, string>;
}

export interface TextProblem {
  question: string;
  solution: string;
}

export interface SubtopicGroup {
  subtopic: string;
  items: SubtopicItem[];
  has_video?: boolean;
}

export interface ChapterDetail {
  subject: string;
  class: number;
  chapter: string;
  subtopics: SubtopicGroup[];
}

export interface ExplanationStep {
  text: string;
  label: string;
  latex: string;
}

export interface Explanation {
  intro: string | null;
  summary: string | null;
  problem_statement: string | null;
  final_answer: string | null;
  steps: ExplanationStep[];
}

export interface WikiImage {
  url: string;
  title: string;
  license: string;
  artist: string;
}

export interface SubtopicPart {
  part_index: number;
  heading: string;
  paragraph: string;
  paragraph_html: string;
  diagram_url: string | null;
  diagram_caption: string | null;
}

export interface ResolveResult {
  status: 'published' | 'local' | 'not_available';
  run_id: string | null;
  youtube_video_id: string | null;
  title: string | null;
  available_languages: string[];
  explanation: Explanation | null;
  ncert_note: string | null;
  ncert_problems: TextProblem[];
  wiki_title: string | null;
  wiki_text: string | null;
  wiki_html?: string | null;
  parts?: SubtopicPart[];
  has_diagrams?: boolean;
  wiki_source_url: string | null;
  wiki_images: WikiImage[];
}

export interface ReviewItem {
  run_id: string;
  subject: string;
  class: number;
  chapter: string;
  subtopic: string;
  content_type: string;
  difficulty: string;
  language: string;
  title: string | null;
  review_comment: string | null;
  created_at: string;
}
