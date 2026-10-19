import { useTranslation } from "react-i18next";
import { useState } from "react";
import { login, register } from "@/features/auth/oidc";
import { errorMessage } from "@/shared/api/authedClient";
export function LoginPage() {
  const { t } = useTranslation("common");
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);
  async function start(action: () => Promise<void>) {
    setPending(true);
    setError("");
    try {
      await action();
    } catch (failure) {
      setError(errorMessage(failure));
      setPending(false);
    }
  }
  return (
    <section className="placeholder-page auth-page">
      <h1>{t("ui.loginTitle")}</h1>
      <p>{t("ui.loginHint")}</p>
      {error && <p role="alert">{error}</p>}
      <button
        className="primary-button"
        disabled={pending}
        onClick={() => void start(login)}
      >
        {t("ui.login")}
      </button>{" "}
      <button disabled={pending} onClick={() => void start(register)}>
        {t("ui.register")}
      </button>
    </section>
  );
}
