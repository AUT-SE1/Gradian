import { adaptPanel, adaptNotifications, adaptStudentDashboard } from '../api/panelAdapters';
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

export function useStudentDashboard() {
  const { session } = useAuth();
  return useQuery({
    queryKey: ['portal', session?.user.id, session?.user.primaryRole, 'student-dashboard'],
    enabled: session?.user.primaryRole === 'student',
    queryFn: async ({ signal }) => {
      if (session?.user.primaryRole !== 'student') throw new Error('Student dashboard requires a student session');
      return adaptStudentDashboard(await authenticatedGet<unknown>('/student/dashboard', session, signal));
    },
  });
}
