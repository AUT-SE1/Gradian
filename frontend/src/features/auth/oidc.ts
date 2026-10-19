import { UserManager, WebStorageStateStore } from "oidc-client-ts";
import { httpClient } from "@/shared/api/httpClient";
import type { AuthConfig } from "@/shared/types/auth";
let managers: Promise<{ signIn: UserManager; signUp: UserManager }> | null =
  null;
export function getManagers() {
  managers ??= (async () => {
    const config = await httpClient.get<AuthConfig>("/auth/config");
    const settings = {
      authority: config.issuer,
      client_id: config.client_id,
      redirect_uri: `${window.location.origin}/auth/callback`,
      post_logout_redirect_uri: config.landing_url,
      response_type: "code",
      scope: "openid",
      automaticSilentRenew: true,
      userStore: new WebStorageStateStore({ store: window.localStorage }),
    };
    const signIn = new UserManager(settings);
    const metadata = await signIn.metadataService.getMetadata();
    const signUp = new UserManager({
      ...settings,
      metadata: {
        ...metadata,
        authorization_endpoint: config.registration_endpoint,
      },
    });
    return { signIn, signUp };
  })().catch((error: unknown) => {
    managers = null;
    throw error;
  });
  return managers;
}
let renewal: ReturnType<UserManager["signinSilent"]> | null = null;
export async function renewSession() {
  const { signIn } = await getManagers();
  renewal ??= signIn.signinSilent().finally(() => {
    renewal = null;
  });
  return renewal;
}
export const login = async () => (await getManagers()).signIn.signinRedirect();
export const register = async () =>
  (await getManagers()).signUp.signinRedirect();
export const logout = async () =>
  (await getManagers()).signIn.signoutRedirect();
let callback: ReturnType<UserManager["signinRedirectCallback"]> | null = null;
// StrictMode mounts twice; an authorization code can only be exchanged once.
export async function finishSignIn() {
  const { signIn } = await getManagers();
  callback ??= signIn.signinRedirectCallback();
  return callback;
}
