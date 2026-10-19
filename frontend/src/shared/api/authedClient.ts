import i18n from "@/shared/i18n/i18n";
import { getManagers, renewSession } from "@/features/auth/oidc";
import { ApiError } from "./ApiError";
import { httpClient } from "./httpClient";
import type { ApiErrorBody } from "@/shared/types/auth";
export function errorBody(error: unknown): ApiErrorBody | null {
  if (!(error instanceof ApiError)) return null;
  const body = error.payload as Partial<ApiErrorBody> | null;
  return body && typeof body.code === "string" ? (body as ApiErrorBody) : null;
}
export function errorMessage(error: unknown) {
  const body = errorBody(error);
  if (body)
    return i18n.language.startsWith("fa")
      ? body.message
      : i18n.t(`errors.${body.code}`, { defaultValue: body.message });
  return i18n.t("ui.connectionError");
}
async function request<T>(
  method: "get" | "post" | "patch" | "delete",
  path: string,
  body?: unknown,
): Promise<T> {
  const { signIn } = await getManagers();
  let user = await signIn.getUser();
  let renewed = false;
  const send = () => {
    const headers = new Headers();
    if (user) headers.set("Authorization", `Bearer ${user.access_token}`);
    const options = { headers };
    return method === "get" || method === "delete"
      ? httpClient[method]<T>(path, options)
      : httpClient[method]<T>(path, body, options);
  };
  try {
    if (user?.expired) {
      try {
        user = await renewSession();
        renewed = true;
      } catch {
        throw new ApiError(401, {
          code: "invalid_token",
          message: "نشست ورود منقضی شده است. دوباره وارد شوید.",
          details: {},
        });
      }
    }
    if (!user)
      throw new ApiError(401, {
        code: "not_authenticated",
        message: "لطفاً دوباره وارد شوید.",
        details: {},
      });
    try {
      return await send();
    } catch (error) {
      if (!(error instanceof ApiError) || error.status !== 401 || renewed)
        throw error;
      try {
        user = await renewSession();
      } catch {
        throw error;
      }
      if (!user) throw error;
      return await send(); // one renewal and one retry only
    }
  } catch (error) {
    if (
      (error instanceof ApiError && error.status === 401) ||
      !user ||
      user.expired
    ) {
      await signIn.removeUser();
      window.dispatchEvent(new Event("gradian:session-lost"));
    }
    if (errorBody(error)?.code === "account_disabled") {
      await signIn.removeUser();
      window.dispatchEvent(
        new CustomEvent("gradian:account-error", { detail: error }),
      );
      // End the identity-provider session as required by the backend contract.
      void signIn
        .signoutRedirect({ id_token_hint: user?.id_token })
        .catch(() => {});
    }
    throw error;
  }
}
export const api = {
  get: <T>(path: string) => request<T>("get", path),
  post: <T>(path: string, body?: unknown) => request<T>("post", path, body),
  patch: <T>(path: string, body: unknown) => request<T>("patch", path, body),
  delete: <T>(path: string) => request<T>("delete", path),
};
