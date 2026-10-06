import type { PortalRole } from './portal';

export type LoginPayload = { mobile: string; password: string };
export type AuthUser = { id: string; displayName: string; primaryRole: PortalRole };
export type AuthSession = { accessToken: string; refreshToken?: string; user: AuthUser };
