import { httpClient } from '@/shared/api/httpClient';
import { ApiError } from '@/shared/api/ApiError';
import type { AuthSession } from '@/shared/types/auth';
import { isUsableSession } from '@/shared/auth/session';
import type { PortalRole } from '@/shared/types/portal';
import {
  createAuthFlowStarter,
  OIDC_FLOW_KEY,
  OIDC_STATE_KEY,
  PKCE_VERIFIER_KEY,
  validateIssuer,
  type AuthConfig,
  type AuthFlow,
} from '@/features/auth/api/authFlow';
import {
  AuthCallbackFailure,
  callbackFailureFromStatus,
  clearCallbackAttempt,
  readCallbackAttempt,
} from '@/features/auth/api/authCallback';

export { AuthCallbackFailure } from '@/features/auth/api/authCallback';
export type { AuthFlow } from '@/features/auth/api/authFlow';

type Me = {
  sub: string;
  mobile: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  role: 'student' | 'consultant' | 'professor' | 'admin';
  consultant_type: '' | 'consultant' | 'top_ranker';
  panel: 'student' | 'consultant' | 'professor' | 'admin';
  home_path: string;
  field_of_study: '' | 'experimental' | 'mathematics' | 'humanities';
  avatar_url: string;
  bio: string;
};

type TokenResponse = {
  access_token: string;
  refresh_token?: string;
  id_token?: string;
  expires_in: number;
  token_type: string;
};

let callbackPromise: Promise<AuthSession> | null = null;

const roleMap: Record<Me['panel'], PortalRole> = {
  student: 'student',
  consultant: 'counsellor',
  professor: 'instructor',
  admin: 'admin',
};

function callbackUrl() {
  return `${window.location.origin}/auth/callback`;
}

async function getConfig() {
  return httpClient.get<AuthConfig>('/auth/config');
}

const authFlowStarter = createAuthFlowStarter({
  getConfig,
  callbackUrl,
  assign: (url) => window.location.assign(url),
  storage: sessionStorage,
});

function validTokenResponse(value: unknown): value is TokenResponse {
  if (!value || typeof value !== 'object') return false;
  const token = value as Partial<TokenResponse>;
  return typeof token.access_token === 'string' && token.access_token.trim().length > 0
    && typeof token.expires_in === 'number' && Number.isFinite(token.expires_in) && token.expires_in > 0
    && typeof token.token_type === 'string' && token.token_type.trim().length > 0
    && (token.refresh_token === undefined || (typeof token.refresh_token === 'string' && token.refresh_token.length > 0))
    && (token.id_token === undefined || (typeof token.id_token === 'string' && token.id_token.length > 0));
}

async function completeLogin(): Promise<AuthSession> {
  let flow: AuthFlow = sessionStorage.getItem(OIDC_FLOW_KEY) === 'registration' ? 'registration' : 'login';
  try {
    const attempt = readCallbackAttempt(window.location.search, sessionStorage);
    flow = attempt.flow;

    const config = await getConfig();
    const issuer = validateIssuer(config.issuer);
    const tokenEndpoint = new URL(`${issuer.origin}${issuer.pathname.replace(/\/+$/, '')}/protocol/openid-connect/token`);
    const body = new URLSearchParams({
      grant_type: 'authorization_code',
      client_id: config.client_id,
      redirect_uri: callbackUrl(),
      code: attempt.code,
      code_verifier: attempt.verifier,
    });

    const tokenResponse = await fetch(tokenEndpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body,
    });
    if (!tokenResponse.ok) throw callbackFailureFromStatus(tokenResponse.status, flow);

    let tokenPayload: unknown;
    try {
      tokenPayload = await tokenResponse.json();
    } catch {
      throw new AuthCallbackFailure('provider', flow);
    }
    if (!validTokenResponse(tokenPayload)) throw new AuthCallbackFailure('failed', flow);
    const tokens = tokenPayload;

    let me: Me;
    try {
      me = await httpClient.get<Me>('/me', {
        headers: { Authorization: `Bearer ${tokens.access_token}` },
      });
    } catch (failure: unknown) {
      if (failure instanceof ApiError) throw callbackFailureFromStatus(failure.status, flow);
      throw new AuthCallbackFailure('provider', flow);
    }

    const primaryRole = Object.hasOwn(roleMap, me.panel) ? roleMap[me.panel] : undefined;
    if (!primaryRole) throw new AuthCallbackFailure('forbidden', flow);

    // Core owns the role decision. Refuse an internally inconsistent /me response rather than
    // routing from an arbitrary path supplied by a stale/misconfigured provider response.
    if (me.home_path && me.home_path !== `/${me.panel}`) {
      throw new AuthCallbackFailure('failed', flow);
    }

    const session: AuthSession = {
      accessToken: tokens.access_token,
      refreshToken: tokens.refresh_token,
      idToken: tokens.id_token,
      expiresAt: Date.now() + (tokens.expires_in * 1000),
      user: {
        id: me.sub,
        displayName: me.full_name || me.mobile,
        primaryRole,
      },
    };
    if (!isUsableSession(session)) throw new AuthCallbackFailure('failed', flow);
    return session;
  } catch (failure: unknown) {
    if (failure instanceof AuthCallbackFailure) throw failure;
    if (failure instanceof ApiError) throw callbackFailureFromStatus(failure.status, flow);
    throw new AuthCallbackFailure('provider', flow);
  } finally {
    // A callback code/state/verifier is one-shot. Success and every terminal error clear it so
    // retry always starts a fresh PKCE flow and a repeated callback cannot consume it again.
    clearCallbackAttempt(sessionStorage);
  }
}

function finishLogin(): Promise<AuthSession> {
  callbackPromise ??= completeLogin().finally(() => {
    callbackPromise = null;
  });
  return callbackPromise;
}

async function retryCallback(flow: AuthFlow) {
  return flow === 'registration'
    ? authFlowStarter.beginRegistration()
    : authFlowStarter.beginLogin();
}

async function logout(idToken?: string) {
  sessionStorage.removeItem(PKCE_VERIFIER_KEY);
  sessionStorage.removeItem(OIDC_STATE_KEY);
  sessionStorage.removeItem(OIDC_FLOW_KEY);
  try {
    const config = await getConfig();
    const url = new URL(config.end_session_url);
    url.searchParams.set('client_id', config.client_id);
    url.searchParams.set('post_logout_redirect_uri', config.landing_url);
    if (idToken) url.searchParams.set('id_token_hint', idToken);
    window.location.assign(url.toString());
  } catch {
    window.location.assign('/');
  }
}

export const authApi = {
  getConfig,
  beginLogin: authFlowStarter.beginLogin,
  beginRegistration: authFlowStarter.beginRegistration,
  finishLogin,
  retryCallback,
  logout,
};
