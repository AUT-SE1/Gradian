import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/app/providers/AuthProvider';
import { authApi } from '@/features/auth/api/authApi';
import { ApiError } from '@/shared/api/ApiError';

type CallbackError = 'forbidden' | 'unauthorized' | 'failed';

export function AuthCallbackPage() {
  const navigate = useNavigate();
  const { t } = useTranslation('auth');
  const { setSession } = useAuth();
  const [error, setError] = useState<CallbackError | null>(null);

  useEffect(() => {
    let active = true;
    authApi.finishLogin()
      .then((session) => {
        if (!active) return;
        setSession(session);
        navigate(`/${session.user.primaryRole}`, { replace: true });
      })
      .catch((failure: unknown) => {
        if (!active) return;
        setSession(null);
        setError(failure instanceof ApiError && failure.status === 403 ? 'forbidden'
          : failure instanceof ApiError && failure.status === 401 ? 'unauthorized' : 'failed');
      });
    return () => { active = false; };
  }, [navigate, setSession]);

  return (
    <div className="auth-page">
      <section className="auth-figma-card auth-redirect-card">
        <h1>{t(error ? `callback.${error}Title` : 'callback.title')}</h1>
        {error ? (
          <>
            <p className="form-error" role="alert">{t(`callback.${error}`)}</p>
            <button className="auth-figma-submit" type="button" onClick={() => navigate('/login', { replace: true })}>{t('retry')}</button>
          </>
        ) : <p className="auth-redirect-message">{t('callback.pending')}</p>}
      </section>
    </div>
  );
}
