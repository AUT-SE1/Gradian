// Test entry only; not included in the production application.
import { useEffect } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider, useAuth } from '@/app/providers/AuthProvider';
import { I18nProvider } from '@/app/providers/I18nProvider';
import { ThemeProvider } from '@/app/providers/ThemeProvider';
import { AppRouter } from '@/app/router/AppRouter';
import { createAppQueryClient } from '@/shared/api/queryClient';
import '@/shared/styles/globals.css';
import '@/shared/styles/portals.css';
const client = createAppQueryClient();
export function Probe() {
 const auth = useAuth();
 useEffect(() => { Object.assign(window, { t05: { auth, client } }); }, [auth]);
 return <AppRouter />;
}
createRoot(document.getElementById('root')!).render(<QueryClientProvider client={client}><I18nProvider><ThemeProvider><AuthProvider><BrowserRouter><Probe /></BrowserRouter></AuthProvider></ThemeProvider></I18nProvider></QueryClientProvider>);
