import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type PropsWithChildren } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import type { AuthSession } from '@/shared/types/auth';
import { isUsableSession, persistSession, readStoredSession, sameIdentity, SESSION_STORAGE_KEY } from '@/shared/auth/session';
import { onUnauthorized } from '@/shared/auth/authEvents';

type AuthContextValue = {
  session: AuthSession | null;
  isAuthenticated: boolean;
  setSession: (session: AuthSession | null) => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);
const MAX_TIMEOUT = 2_147_483_647;

export function AuthProvider({ children }: PropsWithChildren) {
  const queryClient = useQueryClient();
  const [session, setSessionState] = useState<AuthSession | null>(readStoredSession);
  const sessionRef = useRef(session);

  const applySession = useCallback((next: AuthSession | null, persist: boolean) => {
    if (next !== null && !isUsableSession(next)) throw new Error('Invalid or expired authentication session.');
    if (next === null || !sameIdentity(sessionRef.current, next)) {
      // Cancel first, then remove all queries AND mutations. Clearing only data
      // without cancelling could let a late result restore the previous user.
      void queryClient.cancelQueries();
      queryClient.clear();
    }
    sessionRef.current = next;
    if (persist) persistSession(next);
    setSessionState(next);
  }, [queryClient]);

  const setSession = useCallback((next: AuthSession | null) => applySession(next, true), [applySession]);

  useEffect(() => onUnauthorized((token) => {
    if (sessionRef.current?.accessToken === token) setSession(null);
  }), [setSession]);

  useEffect(() => {
    function onStorage(event: StorageEvent) {
      if (event.storageArea === localStorage && (event.key === SESSION_STORAGE_KEY || event.key === null)) {
        applySession(readStoredSession(), false);
      }
    }
    window.addEventListener('storage', onStorage);
    return () => window.removeEventListener('storage', onStorage);
  }, [applySession]);

  useEffect(() => {
    if (!session) return;
    let timer: ReturnType<typeof setTimeout>;
    function checkExpiry() {
      const current = sessionRef.current;
      if (!current) return;
      if (!isUsableSession(current)) {
        setSession(null);
      } else {
        clearTimeout(timer);
        timer = setTimeout(checkExpiry, Math.min(current.expiresAt - Date.now(), MAX_TIMEOUT));
      }
    }
    function onVisibility() {
      if (document.visibilityState === 'visible') checkExpiry();
    }
    checkExpiry();
    window.addEventListener('focus', checkExpiry);
    document.addEventListener('visibilitychange', onVisibility);
    return () => {
      clearTimeout(timer);
      window.removeEventListener('focus', checkExpiry);
      document.removeEventListener('visibilitychange', onVisibility);
    };
  }, [session, setSession]);

  const value = useMemo(
    () => ({ session, isAuthenticated: isUsableSession(session), setSession }),
    [session, setSession],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) throw new Error('useAuth must be used inside AuthProvider');
  return value;
}
