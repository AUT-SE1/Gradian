import { httpClient } from '@/shared/api/httpClient';
import type { AuthSession } from '@/shared/types/auth';
import type { PortalRole } from '@/shared/types/portal';

type AuthConfig = {
  issuer: string;
  realm: string;
  client_id: string;
  registration_endpoint: string;
  end_session_url: string;
  landing_url: string;
};

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

const PKCE_VERIFIER_KEY = 'gradian.auth.pkce_verifier';
const OIDC_STATE_KEY = 'gradian.auth.oidc_state';
let loginStarting = false;
let callbackPromise: Promise<AuthSession> | null = null;

const roleMap: Record<Me['panel'], PortalRole> = {
  student: 'student',
  consultant: 'counsellor',
  professor: 'instructor',
  admin: 'admin',
};

function randomBase64Url(bytes = 32) {
  const values = new Uint8Array(bytes);
  crypto.getRandomValues(values);
  return base64Url(values);
}

function base64Url(bytes: Uint8Array) {
  let binary = '';
  bytes.forEach((value) => { binary += String.fromCharCode(value); });
  return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/g, '');
}

async function codeChallenge(verifier: string) {
  const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(verifier));
  return base64Url(new Uint8Array(digest));
}

function callbackUrl() {
  return `${window.location.origin}/auth/callback`;
}

async function getConfig() {
  return httpClient.get<AuthConfig>('/auth/config');
}

async function beginLogin() {
  if (loginStarting) return;
  loginStarting = true;
  try {
    const config = await getConfig();
  const verifier = randomBase64Url(48);
  const state = randomBase64Url(24);
  const challenge = await codeChallenge(verifier);

  sessionStorage.setItem(PKCE_VERIFIER_KEY, verifier);
  sessionStorage.setItem(OIDC_STATE_KEY, state);

  const authorize = new URL(`${config.issuer}/protocol/openid-connect/auth`);
  authorize.searchParams.set('client_id', config.client_id);
  authorize.searchParams.set('response_type', 'code');
  authorize.searchParams.set('scope', 'openid');
  authorize.searchParams.set('redirect_uri', callbackUrl());
  authorize.searchParams.set('code_challenge', challenge);
  authorize.searchParams.set('code_challenge_method', 'S256');
  authorize.searchParams.set('state', state);

    window.location.assign(authorize.toString());
  } catch (error) {
    loginStarting = false;
    throw error;
  }
}

async function completeLogin(): Promise<AuthSession> {
  const params = new URLSearchParams(window.location.search);
  const error = params.get('error');
  if (error) throw new Error(params.get('error_description') || error);

  const code = params.get('code');
  const returnedState = params.get('state');
  const verifier = sessionStorage.getItem(PKCE_VERIFIER_KEY);
  const expectedState = sessionStorage.getItem(OIDC_STATE_KEY);

  if (!code || !verifier || !returnedState || returnedState !== expectedState) {
    throw new Error('Invalid authentication callback.');
  }

  const config = await getConfig();
  const tokenEndpoint = `${config.issuer}/protocol/openid-connect/token`;
  const body = new URLSearchParams({
    grant_type: 'authorization_code',
    client_id: config.client_id,
    redirect_uri: callbackUrl(),
    code,
    code_verifier: verifier,
  });

  const tokenResponse = await fetch(tokenEndpoint, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body,
  });
  if (!tokenResponse.ok) throw new Error('Token exchange failed.');
  const tokens = await tokenResponse.json() as TokenResponse;

  sessionStorage.removeItem(PKCE_VERIFIER_KEY);
  sessionStorage.removeItem(OIDC_STATE_KEY);

  const me = await httpClient.get<Me>('/me', {
    headers: { Authorization: `Bearer ${tokens.access_token}` },
  });
  const primaryRole = roleMap[me.panel];

  return {
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
}

function finishLogin(): Promise<AuthSession> {
  callbackPromise ??= completeLogin().catch((error) => {
    callbackPromise = null;
    throw error;
  });
  return callbackPromise;
}

async function logout(idToken?: string) {
  sessionStorage.removeItem(PKCE_VERIFIER_KEY);
  sessionStorage.removeItem(OIDC_STATE_KEY);
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

export const authApi = { getConfig, beginLogin, finishLogin, logout };
