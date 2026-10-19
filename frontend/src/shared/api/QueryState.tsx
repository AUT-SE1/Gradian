import { useTranslation } from "react-i18next";
import { errorMessage } from "./authedClient";
export function QueryState({
  pending,
  error,
  retry,
}: {
  pending: boolean;
  error: unknown;
  retry: () => unknown;
}) {
  const { t } = useTranslation("common");
  if (pending) return <p role="status">{t("ui.loading")}</p>;
  if (error)
    return (
      <div role="alert">
        <p>{errorMessage(error)}</p>
        <button onClick={() => void retry()}>{t("ui.retry")}</button>
      </div>
    );
  return null;
}
