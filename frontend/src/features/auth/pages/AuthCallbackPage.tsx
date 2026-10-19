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
  );
}
