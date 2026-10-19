import { api } from "@/shared/api/authedClient";
import type {
  PanelInfo,
  Page,
  ServiceEntry,
  Dashboard,
  NotificationList,
} from "@/shared/types/content";
export const portalApi = {
  panel: () => api.get<PanelInfo>("/panel"),
  services: () => api.get<Page<ServiceEntry>>("/panel/services"),
  dashboard: () => api.get<Dashboard>("/student/dashboard"),
  notifications: (offset = 0) =>
    api.get<NotificationList>(`/notifications?limit=20&offset=${offset}`),
};
export function serviceUrl(service: ServiceEntry): string | null {
  if (service.status !== "available" || !service.url) return null;
  try {
    const url = new URL(service.url, window.location.origin);
    return ["http:", "https:"].includes(url.protocol) ? url.href : null;
  } catch {
    return null;
  }
}
