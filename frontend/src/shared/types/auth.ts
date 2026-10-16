import type { PortalRole } from './portal';

export type AuthUser = {
  id: string;
  displayName: string;
  primaryRole: PortalRole;
};

export type AuthSession = {
  accessToken: string;
  refreshToken?: string;
  idToken?: string;
  expiresAt?: number;
  user: AuthUser;
};
