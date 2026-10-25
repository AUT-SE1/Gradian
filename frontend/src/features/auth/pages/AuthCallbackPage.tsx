import { useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/app/providers/AuthProvider';
import {
  AuthCallbackFailure,
  authApi,
  type AuthFlow,
} from '@/features/auth/api/authApi';
import type { CallbackFailureKind } from '@/features/auth/api/authCallback';

export function AuthCallbackPage() {
  const { t } = useTranslation('auth');
  const { setSession } = useAuth();
  const [error, setError] = useState<CallbackFailureKind | null>(null);
  const [retryFlow, setRetryFlow] = useState<AuthFlow>('login');
  const [retrying, setRetrying] = useState(false);
  const errorRef = useRef<HTMLParagraphElement>(null);

  useEffect(() => {
    let active = true;

    setSession(null);

    authApi.finishLogin()
      .then((session) => {
        if (!active) return;
        setSession(session);
        window.location.replace(`/${session.user.primaryRole}`);
      })
      .catch((failure: unknown) => {
        if (!active) return;
        setSession(null);
        if (failure instanceof AuthCallbackFailure) {
          setRetryFlow(failure.retryFlow);
          setError(failure.kind);
        } else {
          setError('failed');
        }
      });
    return () => { active = false; };
  }, [setSession]);

  useEffect(() => {
    if (error) errorRef.current?.focus();
  }, [error]);

  async function handleRetry() {
    if (retrying) return;
    setRetrying(true);
    setError(null);
    try {
      const started = await authApi.retryCallback(retryFlow);
      if (!started) {
        setRetrying(false);
        setError('failed');
      }
    } catch {
      setRetrying(false);
      setError('provider');
    }
  }

  return (
    <div className="auth-page">
      <section className="auth-figma-card auth-redirect-card" aria-busy={!error}>
        <h1>{t(error ? `callback.${error}Title` : 'callback.title')}</h1>
        {error ? (
          <>
            <p ref={errorRef} className="form-error" role="alert" tabIndex={-1} aria-atomic="true">
              {t(`callback.${error}`)}
            </p>
            <button
              className="auth-figma-submit"
              disabled={retrying}
              aria-disabled={retrying}
              type="button"
              onClick={handleRetry}
            >
              {t(retrying ? 'callback.retrying' : 'retry')}
            </button>
          </>
        ) : (
          <p className="auth-redirect-message" role="status" aria-live="polite" aria-atomic="true">
            {t(retrying ? 'callback.retrying' : 'callback.pending')}
          </p>
        )}
      </section>
    </div>
  );
}
