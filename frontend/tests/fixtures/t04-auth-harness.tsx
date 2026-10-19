// Test-only entry. This is never imported by the application or its build.
import { useEffect } from 'react';
import { createRoot } from 'react-dom/client';
import { QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider, useAuth } from '@/app/providers/AuthProvider';
import { createAppQueryClient } from '@/shared/api/queryClient';
import { httpClient } from '@/shared/api/httpClient';
import { authApi } from '@/features/auth/api/authApi';

const client = createAppQueryClient();
export function Probe() {
  const auth = useAuth();
  useEffect(() => {
    Object.assign(window, { t04: { auth, client, httpClient, authApi } });
    document.body.dataset.ready = 'true';
  }, [auth]);
  return <output>{auth.session?.user.id ?? 'anonymous'}</output>;
}

createRoot(document.getElementById('fixture-root')!).render(
  <QueryClientProvider client={client}><AuthProvider><Probe /></AuthProvider></QueryClientProvider>,
);
