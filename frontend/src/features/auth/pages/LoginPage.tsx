import { useEffect, useState } from 'react';
import { Navigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/app/providers/AuthProvider';
import { authApi } from '@/features/auth/api/authApi';

export function LoginPage() {
  const { t } = useTranslation('auth');
  const { session } = useAuth();
  const [error, setError] = useState(false);

  useEffect(() => {
    if (session) return;
    let active = true;
    authApi.beginLogin().catch(() => {
      if (active) setError(true);
    });
    return () => { active = false; };
  }, [session]);

  if (session) return <Navigate to={`/${session.user.primaryRole}`} replace />;

  return (
    <div className="auth-page">
      <section className="auth-figma-card auth-redirect-card">
        <h1>{t('title')}</h1>
        {!error ? (
          <p className="auth-redirect-message">در حال انتقال به صفحه ورود امن...</p>
        ) : (
          <>
            <div className="form-error" role="alert">اتصال به سرویس ورود برقرار نشد.</div>
            <button className="auth-figma-submit" type="button" onClick={() => authApi.beginLogin()}>
              تلاش دوباره
            </button>
          </>
        )}
      </section>
    </div>
  );
}
