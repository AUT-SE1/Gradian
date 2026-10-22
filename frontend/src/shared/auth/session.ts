import type { AuthSession } from '@/shared/types/auth';
import type { PortalRole } from '@/shared/types/portal';

export const SESSION_STORAGE_KEY = 'gradian.auth.session';
const ROLES: readonly string[] = ['student', 'instructor', 'counsellor', 'admin'];
const nonEmpty = (value: unknown): value is string => typeof value === 'string' && value.trim().length > 0;

export function isPortalRole(value: unknown): value is PortalRole {
  return typeof value === 'string' && ROLES.includes(value);
}

export function isUsableSession(value: unknown, now = Date.now()): value is AuthSession {
  if (!value || typeof value !== 'object') return false;
  const session = value as Partial<AuthSession>;
  return nonEmpty(session.accessToken)
    && typeof session.expiresAt === 'number' && Number.isFinite(session.expiresAt) && session.expiresAt > now
    && Boolean(session.user && typeof session.user === 'object'
      && nonEmpty(session.user.id) && typeof session.user.displayName === 'string'
      && isPortalRole(session.user.primaryRole))
    && (session.refreshToken === undefined || nonEmpty(session.refreshToken))
    && (session.idToken === undefined || nonEmpty(session.idToken));
}

export function sameIdentity(a: AuthSession | null, b: AuthSession | null): boolean {
  return a?.user.id === b?.user.id && a?.user.primaryRole === b?.user.primaryRole;
}

export function readStoredSession(): AuthSession | null {
  try {
    const raw = localStorage.getItem(SESSION_STORAGE_KEY);
    if (raw === null) return null;
    const value: unknown = JSON.parse(raw);
    if (isUsableSession(value)) return value;
  } catch { /* Invalid JSON or unavailable storage: no authenticated session. */ }
  persistSession(null);
  return null;
}

export function persistSession(session: AuthSession | null) {
  try {
    if (session) localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(session));
    else localStorage.removeItem(SESSION_STORAGE_KEY);
  } catch { /* The in-memory session still works when browser storage is unavailable. */ }
}
