import { httpClient } from '@/shared/api/httpClient';
import type { AuthSession, LoginPayload } from '@/shared/types/auth';

export const authApi = {
  login: (payload: LoginPayload) => httpClient.post<AuthSession>('/auth/login/', payload),
};
