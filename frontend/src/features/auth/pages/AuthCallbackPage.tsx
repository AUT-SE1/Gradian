import { useTranslation } from "react-i18next";
import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "@/app/providers/AuthProvider";
import { finishSignIn } from "@/features/auth/oidc";
import { errorMessage } from "@/shared/api/authedClient";
export function AuthCallbackPage() {
  const { t } = useTranslation("common");
  const { reload } = useAuth();
  const navigate = useNavigate();
  const [error, setError] = useState("");
  useEffect(() => {
    let active = true;
    void finishSignIn()
      .then(() => reload())
      .then((me) => {
        if (active) navigate(me.home_path, { replace: true });
      })
      .catch((failure: unknown) => {
        if (active) setError(errorMessage(failure));
      });
    return () => {
      active = false;
    };
  }, [reload, navigate]);
  return (
    <section className="placeholder-page">
      {error ? (
        <>
          <p role="alert">{error}</p>
          <Link to="/login">{t("ui.backToLogin")}</Link>
        </>
      ) : (
        <p role="status">{t("ui.callbackLoading")}</p>
      )}
    </section>
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/app/providers/AuthProvider';
import { authApi } from '@/features/auth/api/authApi';

export function AuthCallbackPage() {
  const navigate = useNavigate();
  const { setSession } = useAuth();
  const [error, setError] = useState(false);

  useEffect(() => {
    let active = true;
    authApi.finishLogin()
      .then((session) => {
        if (!active) return;
        setSession(session);
        navigate(`/${session.user.primaryRole}`, { replace: true });
      })
      .catch(() => {
        if (active) setError(true);
      });
    return () => { active = false; };
  }, [navigate, setSession]);

  return (
    <div className="auth-page">
      <section className="auth-figma-card auth-redirect-card">
        <h1>{error ? 'خطا در ورود' : 'در حال تکمیل ورود'}</h1>
        {error ? (
          <button className="auth-figma-submit" type="button" onClick={() => navigate('/login', { replace: true })}>
            تلاش دوباره
          </button>
        ) : (
          <p className="auth-redirect-message">لطفاً چند لحظه صبر کنید...</p>
        )}
      </section>
    </div>
  );
}
