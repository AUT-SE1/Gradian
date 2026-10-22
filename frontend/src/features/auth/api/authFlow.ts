export type AuthConfig = {
  issuer: string;
  realm: string;
  client_id: string;
  registration_endpoint: string;
  end_session_url: string;
  landing_url: string;
};

export type AuthFlow = 'login' | 'registration';

type StorageLike = Pick<Storage, 'setItem'>;

type AuthFlowDependencies = {
  getConfig: () => Promise<AuthConfig>;
  callbackUrl: () => string;
  assign: (url: string) => void;
  storage: StorageLike;
};

export const PKCE_VERIFIER_KEY = 'gradian.auth.pkce_verifier';
export const OIDC_STATE_KEY = 'gradian.auth.oidc_state';
export const OIDC_FLOW_KEY = 'gradian.auth.oidc_flow';

function base64Url(bytes: Uint8Array) {
  let binary = '';
  bytes.forEach((value) => { binary += String.fromCharCode(value); });
  return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/g, '');
}

function randomBase64Url(bytes = 32) {
  const values = new Uint8Array(bytes);
  crypto.getRandomValues(values);
  return base64Url(values);
}

async function codeChallenge(verifier: string) {
  const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(verifier));
  return base64Url(new Uint8Array(digest));
}

export function validateIssuer(rawIssuer: string) {
  let issuer: URL;
  try {
    issuer = new URL(rawIssuer);
  } catch {
    throw new Error('Invalid identity provider configuration.');
  }

  if (!['http:', 'https:'].includes(issuer.protocol)
    || issuer.username
    || issuer.password
    || issuer.search
    || issuer.hash) {
    throw new Error('Invalid identity provider configuration.');
  }
  return issuer;
}

function oidcEndpoint(config: AuthConfig, flow: AuthFlow) {
  if (!config.client_id?.trim()) {
    throw new Error('Invalid identity provider configuration.');
  }

  const issuer = validateIssuer(config.issuer);
  const issuerPath = issuer.pathname.replace(/\/+$/, '');

  if (flow === 'login') {
    return new URL(`${issuer.origin}${issuerPath}/protocol/openid-connect/auth`);
  }

  let registration: URL;
  try {
    registration = new URL(config.registration_endpoint);
  } catch {
    throw new Error('Invalid registration endpoint.');
  }

  const expectedPath = `${issuerPath}/protocol/openid-connect/registrations`;
  if (!['http:', 'https:'].includes(registration.protocol)
    || registration.username
    || registration.password
    || registration.search
    || registration.hash
    || registration.origin !== issuer.origin
    || registration.pathname.replace(/\/+$/, '') !== expectedPath) {
    throw new Error('Invalid registration endpoint.');
  }
  return registration;
}

async function buildAuthorizationUrl(config: AuthConfig, flow: AuthFlow, callbackUrl: string) {
  const endpoint = oidcEndpoint(config, flow);
  const verifier = randomBase64Url(48);
  const state = randomBase64Url(24);
  const challenge = await codeChallenge(verifier);

  endpoint.searchParams.set('client_id', config.client_id);
  endpoint.searchParams.set('response_type', 'code');
  endpoint.searchParams.set('scope', 'openid');
  endpoint.searchParams.set('redirect_uri', callbackUrl);
  endpoint.searchParams.set('code_challenge', challenge);
  endpoint.searchParams.set('code_challenge_method', 'S256');
  endpoint.searchParams.set('state', state);

  return { url: endpoint.toString(), verifier, state };
}

export function createAuthFlowStarter(dependencies: AuthFlowDependencies) {
  let starting = false;

  async function begin(flow: AuthFlow) {
    // StrictMode effects and double clicks can call the starter more than once before navigation.
    // Keep exactly one PKCE pair alive so a second call cannot overwrite verifier/state.
    if (starting) return false;
    starting = true;

    try {
      const config = await dependencies.getConfig();
      const authorization = await buildAuthorizationUrl(config, flow, dependencies.callbackUrl());

      // Do not persist PKCE material until config/endpoint validation has succeeded. The verifier
      // is intentionally storage-only and never becomes part of the redirect URL.
      dependencies.storage.setItem(PKCE_VERIFIER_KEY, authorization.verifier);
      dependencies.storage.setItem(OIDC_STATE_KEY, authorization.state);
      dependencies.storage.setItem(OIDC_FLOW_KEY, flow);
      dependencies.assign(authorization.url);
      // `starting` protects only one in-flight start. Browsers may restore this document from
      // bfcache when the user presses Back from Keycloak, so keeping the module-level lock set
      // forever would make a deliberate retry impossible on the restored page.
      starting = false;
      return true;
    } catch (error) {
      // The browser did not leave this page, so a user-visible retry must be able to start fresh.
      starting = false;
      throw error;
    }
  }

  return {
    beginLogin: () => begin('login'),
    beginRegistration: () => begin('registration'),
  };
}
