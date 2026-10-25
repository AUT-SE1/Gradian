import { useEffect, useRef, useState } from 'react';
import { Navigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/app/providers/AuthProvider';
import { authApi } from '@/features/auth/api/authApi';
import { isUsableSession } from '@/shared/auth/session';

type LoginStartStatus = 'starting' | 'error';

export function LoginPage() {
  const { t } = useTranslation('auth');
  const { session } = useAuth();
  const [status, setStatus] = useState<LoginStartStatus>('starting');
  const [retrying, setRetrying] = useState(false);
  const errorRef = useRef<HTMLDivElement>(null);
  const hasSession = isUsableSession(session);

  useEffect(() => {
    if (hasSession || status !== 'starting') return;
    let active = true;

    authApi.beginLogin()
      .then((started) => {
        if (active && !started) setStatus('error');
      })
      .catch(() => {
        if (active) setStatus('error');
      });

    return () => { active = false; };
  }, [hasSession, status]);

  useEffect(() => {
    if (status === 'error') errorRef.current?.focus();
  }, [status]);

  if (hasSession && session) return <Navigate to={`/${session.user.primaryRole}`} replace />;

  async function handleRetry() {
    if (retrying) return;
    setRetrying(true);
    setStatus('starting');
    try {
      const started = await authApi.beginLogin();
      if (!started) {
        setRetrying(false);
        setStatus('error');
      }
    } catch {
      setRetrying(false);
      setStatus('error');
    }
  }

  return (
    <div className="auth-page">
      <section className="auth-figma-card auth-redirect-card" aria-busy={status === 'starting'}>
        <h1>{t('title')}</h1>
        {status === 'starting' ? (
          <p className="auth-redirect-message" role="status" aria-live="polite" aria-atomic="true">
            {t(retrying ? 'retrying' : 'pending')}
          </p>
        ) : (
          <>
            <div ref={errorRef} className="form-error" role="alert" tabIndex={-1} aria-atomic="true">
              {t('connectionError')}
            </div>
            <button
              className="auth-figma-submit"
              disabled={retrying}
              aria-disabled={retrying}
              type="button"
              onClick={handleRetry}
            >
              {t(retrying ? 'retrying' : 'retry')}
            </button>
          </>
        )}
      </section>
    </div>
  );
}
