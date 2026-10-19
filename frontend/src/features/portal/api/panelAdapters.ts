import i18n from '@/shared/i18n/i18n';
import type { Panel, Notifications, Page, Service, Countdown } from './panelApi';

const record = (value: unknown): value is Record<string, unknown> => !!value && typeof value === 'object' && !Array.isArray(value);
const textOrNull = (value: unknown) => value === null || typeof value === 'string';
const integer = (value: unknown) => Number.isInteger(value) && Number(value) >= 0;
function invalid(): never { throw new Error('Invalid panel API response'); }
export function adaptPanel(value: unknown): Panel {
  if (!record(value) || !['student', 'consultant', 'professor', 'admin'].includes(String(value.panel)) || typeof value.home_path !== 'string') return invalid();
  const h = value.header, c = value.countdown;
  if (!record(h) || typeof h.full_name !== 'string' || typeof h.avatar_url !== 'string' || !(h.consultant_type === null || h.consultant_type === 'consultant' || h.consultant_type === 'top_ranker') || !textOrNull(h.field_of_study) || !textOrNull(h.field_of_study_label)) return invalid();
  if (!record(c) || typeof c.date !== 'string' || !Number.isFinite(Date.parse(c.date)) || !['upcoming', 'today', 'past'].includes(String(c.state)) || !integer(c.days_remaining) || typeof c.label !== 'string') return invalid();
  return value as Panel;
}
function page(value: unknown): value is Page<unknown> {
  return record(value) && integer(value.count) && textOrNull(value.next) && textOrNull(value.previous) && Array.isArray(value.results);
}
export function adaptServices(value: unknown): Page<Service> {
  if (!page(value) || !value.results.every(s => record(s) && ['key', 'title_fa', 'title_en', 'description', 'button_label', 'icon'].every(k => typeof s[k] === 'string') && integer(s.order) && ['available', 'unavailable'].includes(String(s.status)) && ['redirect', 'embed'].includes(String(s.mode)) && textOrNull(s.url))) return invalid();
  return value as Page<Service>;
}
export function adaptNotifications(value: unknown): Notifications {
  if (!page(value) || !record(value) || !integer((value as unknown as Record<string, unknown>).unread_count) || !value.results.every(n => record(n) && integer(n.id) && typeof n.title === 'string' && typeof n.body === 'string' && typeof n.created_at === 'string' && Number.isFinite(Date.parse(n.created_at)) && typeof n.is_read === 'boolean')) return invalid();
  return value as Notifications;
}
export function countdownText(countdown: Countdown, language: string): string {
  if (language.startsWith('fa')) return countdown.label;
  if (countdown.state === 'today') return i18n.t('navigation:countdownToday', { lng: language });
  if (countdown.state === 'past') return i18n.t('navigation:countdownPast', { lng: language });
  return i18n.t('navigation:countdownUpcoming', { lng: language, count: countdown.days_remaining });
}
