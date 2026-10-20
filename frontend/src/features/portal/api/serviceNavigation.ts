import { ApiError } from '@/shared/api/ApiError';
import { serviceHref, type Service } from './panelApi';

type ServiceQuery = { isPending: boolean; error: Error | null };
// The registry does not expose a per-entry forbidden status. A 403 applies to
// the service list; a missing entry is unavailable, never an invented permission.
export function serviceStateKey(query: ServiceQuery, service?: Service) {
  if (query.error instanceof ApiError && query.error.status === 403) return 'dataForbidden';
  if (query.error instanceof ApiError && query.error.status === 401) return 'dataUnauthorized';
  if (query.error) return 'dataError';
  if (query.isPending) return 'dataLoading';
  return serviceHref(service) ? 'serviceAvailable' : 'serviceUnavailable';
}
