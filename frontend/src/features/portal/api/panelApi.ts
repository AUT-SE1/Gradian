import { adaptServices } from './panelAdapters';
import { httpClient } from '@/shared/api/httpClient';
import type { AuthSession } from '@/shared/types/auth';

export type Countdown = { date: string; state: 'upcoming' | 'today' | 'past'; days_remaining: number; label: string };
export type Panel = {
  panel: 'student' | 'consultant' | 'professor' | 'admin'; home_path: string;
  header: { full_name: string; avatar_url: string; consultant_type: 'consultant' | 'top_ranker' | null; field_of_study: string | null; field_of_study_label: string | null };
  countdown: Countdown;
};
export type Service = { key: string; title_fa: string; title_en: string; description: string; button_label: string; icon: string; order: number; status: 'available' | 'unavailable'; mode: 'redirect' | 'embed'; url: string | null };
export type Notification = { id: number; title: string; body: string; created_at: string; is_read: boolean };
export type Page<T> = { count: number; next: string | null; previous: string | null; results: T[] };
export type Notifications = Page<Notification> & { unread_count: number };

// Never follow pagination URLs with a bearer token: construct requests against
// our configured API using the documented limit/offset parameters only.
export const PAGE_SIZE = 50;
export function authenticatedGet<T>(path: string, session: AuthSession, signal: AbortSignal) {
  return httpClient.get<T>(path, { signal, headers: { Authorization: `Bearer ${session.accessToken}` } });
}
export async function getServices(session: AuthSession, signal: AbortSignal): Promise<Service[]> {
  const results: Service[] = [];
  let offset = 0;
  for (;;) {
    const page = adaptServices(await authenticatedGet<unknown>(`/panel/services?limit=${PAGE_SIZE}&offset=${offset}`, session, signal));
    if (!Array.isArray(page.results)) throw new Error('Invalid service page');
    results.push(...page.results);
    if (!page.next) return results;
    if (!page.results.length) throw new Error('Invalid service pagination');
    offset += page.results.length;
  }
}
export function serviceHref(service?: Service): string | undefined {
  if (service?.status !== 'available' || !service.url) return undefined;
  try {
    const url = new URL(service.url, window.location.origin);
    if (!['http:', 'https:'].includes(url.protocol) || url.username || url.password) return undefined;
    return url.href;
  } catch { return undefined; }
}

// Shapes from panels/content.py and panels/serializers.py; content blocks may be deleted.
export type StudentDashboard = {
  welcome: { message: string; tip: string } | null;
  countdown: Countdown | null;
  study_streak: { current_days: number; best_days: number; message: string; week: { day: string; done: boolean }[] } | null;
  experience_feed: { id: number; author: string; author_title: string; title: string; excerpt: string; likes: number; comments: number }[] | null;
};
