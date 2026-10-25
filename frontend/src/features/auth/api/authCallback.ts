import {
  OIDC_FLOW_KEY,
  OIDC_STATE_KEY,
  PKCE_VERIFIER_KEY,
  type AuthFlow,
} from './authFlow';

export type CallbackFailureKind =
  | 'cancelled'
  | 'invalid'
  | 'unauthorized'
  | 'forbidden'
  | 'conflict'
  | 'provider'
  | 'failed';

type CallbackStorage = Pick<Storage, 'getItem' | 'removeItem'>;

export type CallbackAttempt = {
  flow: AuthFlow;
  code: string;
  verifier: string;
};

export class AuthCallbackFailure extends Error {
  constructor(
    public readonly kind: CallbackFailureKind,
    public readonly retryFlow: AuthFlow,
  ) {
    super(kind);
    this.name = 'AuthCallbackFailure';
  }
}

export function currentAuthFlow(storage: Pick<Storage, 'getItem'>): AuthFlow {
  return storage.getItem(OIDC_FLOW_KEY) === 'registration' ? 'registration' : 'login';
}

export function readCallbackAttempt(search: string, storage: Pick<Storage, 'getItem'>): CallbackAttempt {
  const flow = currentAuthFlow(storage);
  const params = new URLSearchParams(search);
  const returnedState = params.get('state');
  const expectedState = storage.getItem(OIDC_STATE_KEY);

  // Even provider errors must belong to the flow we started. Never trust an unsolicited callback.
  if (!returnedState || !expectedState || returnedState !== expectedState) {
    throw new AuthCallbackFailure('invalid', flow);
  }

  const providerError = params.get('error');
  if (providerError) {
    throw new AuthCallbackFailure(providerError === 'access_denied' ? 'cancelled' : 'provider', flow);
  }

  const code = params.get('code');
  const verifier = storage.getItem(PKCE_VERIFIER_KEY);
  if (!code || !verifier) throw new AuthCallbackFailure('invalid', flow);
  return { flow, code, verifier };
}

export function clearCallbackAttempt(storage: CallbackStorage) {
  storage.removeItem(PKCE_VERIFIER_KEY);
  storage.removeItem(OIDC_STATE_KEY);
  storage.removeItem(OIDC_FLOW_KEY);
}

export function callbackFailureFromStatus(status: number, flow: AuthFlow) {
  if (status === 400) return new AuthCallbackFailure('invalid', flow);
  if (status === 401) return new AuthCallbackFailure('unauthorized', flow);
  if (status === 403) return new AuthCallbackFailure('forbidden', flow);
  if (status === 409) return new AuthCallbackFailure('conflict', flow);
  if (status === 502 || status === 503 || status === 504) {
    return new AuthCallbackFailure('provider', flow);
  }
  return new AuthCallbackFailure('failed', flow);
}
