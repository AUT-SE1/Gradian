import { createContext, useContext, useMemo, useState, type PropsWithChildren } from 'react';
import type { AuthSession } from '@/shared/types/auth';

type AuthContextValue = {
  session: AuthSession | null;
  isAuthenticated: boolean;
  setSession: (session: AuthSession | null) => void;
};
const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: PropsWithChildren) {
  const [session, setSession] = useState<AuthSession | null>(null);
  const value = useMemo(() => ({ session, isAuthenticated: Boolean(session), setSession }), [session]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) throw new Error('useAuth must be used inside AuthProvider');
  return value;
}
