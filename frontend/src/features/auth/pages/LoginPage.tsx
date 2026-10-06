import { FormEvent, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { authApi } from '@/features/auth/api/authApi';
import { useAuth } from '@/app/providers/AuthProvider';

export function LoginPage() {
  const { t } = useTranslation('auth');
  const { setSession } = useAuth();
  const navigate = useNavigate();
  const [mobile, setMobile] = useState('');
  const [password, setPassword] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmitting(true);
    try {
      const session = await authApi.login({ mobile, password });
      setSession(session);
      navigate(`/${session.user.primaryRole}`);
    } catch {
      // Login UI is intentionally minimal; map ApiError to a shared form error in the next step.
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <section className="placeholder-page auth-page">
      <h1>{t('title')}</h1>
      <form className="auth-form" onSubmit={handleSubmit}>
        <label>{t('mobile')}<input value={mobile} onChange={(event) => setMobile(event.target.value)} /></label>
        <label>{t('password')}<input type="password" value={password} onChange={(event) => setPassword(event.target.value)} /></label>
        <button className="primary-button" disabled={isSubmitting} type="submit">{isSubmitting ? t('submitting') : t('submit')}</button>
      </form>
    </section>
  );
}
