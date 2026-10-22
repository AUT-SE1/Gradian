import { QueryClient } from '@tanstack/react-query';
import { ApiError } from './ApiError';

export function createAppQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 30_000,
        retry: (failureCount, error) => !(error instanceof ApiError && [401, 403].includes(error.status)) && failureCount < 1,
      },
    },
  });
}
