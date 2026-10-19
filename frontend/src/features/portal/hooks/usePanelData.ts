import { adaptPanel, adaptNotifications } from '../api/panelAdapters';
import { useQuery } from '@tanstack/react-query';
import { useAuth } from '@/app/providers/AuthProvider';
import { authenticatedGet, getServices, PAGE_SIZE } from '../api/panelApi';

export function usePanelData() {
  const { session } = useAuth();
  return useQuery({
    queryKey: ['portal', session?.user.id, session?.user.primaryRole, 'panel'],
    enabled: !!session,
    queryFn: async ({ signal }) => adaptPanel(await authenticatedGet<unknown>('/panel', session!, signal)),
  });
}
export function usePanelServices() {
  const { session } = useAuth();
  return useQuery({
    queryKey: ['portal', session?.user.id, session?.user.primaryRole, 'services'],
    enabled: !!session,
    queryFn: ({ signal }) => getServices(session!, signal),
  });
}
export function useNotifications(offset = 0) {
  const { session } = useAuth();
  return useQuery({
    queryKey: ['portal', session?.user.id, session?.user.primaryRole, 'notifications', offset],
    enabled: !!session,
    queryFn: async ({ signal }) => adaptNotifications(await authenticatedGet<unknown>(`/notifications?limit=${PAGE_SIZE}&offset=${offset}`, session!, signal)),
  });
}
