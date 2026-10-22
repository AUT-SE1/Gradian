import { useEffect, useRef, useState } from 'react';
import { Navigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/app/providers/AuthProvider';
import { authApi } from '@/features/auth/api/authApi';
import {
  OIDC_FLOW_KEY,
  OIDC_STATE_KEY,
  PKCE_VERIFIER_KEY,
} from '@/features/auth/api/authFlow';
import { clearCallbackAttempt } from '@/features/auth/api/authCallback';
import { isUsableSession } from '@/shared/auth/session';

type RegistrationStartStatus = 'starting' | 'returned' | 'error';

function hasPendingRegistrationAttempt() {
  try {
    return sessionStorage.getItem(OIDC_FLOW_KEY) === 'registration'
      && Boolean(sessionStorage.getItem(OIDC_STATE_KEY))
      && Boolean(sessionStorage.getItem(PKCE_VERIFIER_KEY));
  } catch {
    return false;
  }
}

export function RegisterPage() {
  const { t } = useTranslation('auth');
  const { session } = useAuth();
  const [status, setStatus] = useState<RegistrationStartStatus>(() => (
    hasPendingRegistrationAttempt() ? 'returned' : 'starting'
  ));
  const [retrying, setRetrying] = useState(false);
  const messageRef = useRef<HTMLDivElement>(null);

  const hasSession = isUsableSession(session);

  useEffect(() => {
    if (hasSession || status !== 'starting') return;
    let active = true;

    authApi.beginRegistration()
      .then((started) => {
        if (active && !started) setStatus('error');
      })
      .catch(() => {
        if (active) setStatus('error');
      });

    return () => { active = false; };
  }, [hasSession, status]);

  useEffect(() => {
    if (status === 'returned' || status === 'error') messageRef.current?.focus();
  }, [status]);

  if (hasSession && session) return <Navigate to={`/${session.user.primaryRole}`} replace />;

  async function handleRetry() {
    if (retrying) return;
    setRetrying(true);
    setStatus('starting');
    clearCallbackAttempt(sessionStorage);
    try {
      const started = await authApi.beginRegistration();
      if (!started) {
        setRetrying(false);
        setStatus('error');
      }
    } catch {
      setRetrying(false);
      setStatus('error');
    }
  }

  const showAction = status === 'returned' || status === 'error';

  return (
    <div className="auth-page">
      <section className="auth-figma-card auth-redirect-card" aria-busy={status === 'starting'}>
        <h1>{t('registration.title')}</h1>
        {!showAction ? (
          <p className="auth-redirect-message" role="status" aria-live="polite" aria-atomic="true">
            {t(retrying ? 'registration.retrying' : 'registration.pending')}
          </p>
        ) : (
          <>
            <div
              ref={messageRef}
              className={status === 'error' ? 'form-error' : 'auth-redirect-message auth-info-message'}
              role={status === 'error' ? 'alert' : 'status'}
              aria-live={status === 'error' ? 'assertive' : 'polite'}
              aria-atomic="true"
              tabIndex={-1}
            >
              {t(status === 'returned' ? 'registration.returned' : 'registration.error')}
            </div>
            <button
              className="auth-figma-submit"
              disabled={retrying}
              aria-disabled={retrying}
              type="button"
              onClick={handleRetry}
            >
              {t(retrying ? 'registration.retrying' : status === 'returned' ? 'registration.continue' : 'retry')}
            </button>
          </>
        )}
      </section>
    </div>
  );
}
