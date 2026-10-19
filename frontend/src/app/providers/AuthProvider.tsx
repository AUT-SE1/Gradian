import { ApiError } from "@/shared/api/ApiError";
import {
  createContext,
  useContext,
  useCallback,
  useEffect,
  useState,
  useRef,
  type PropsWithChildren,
} from "react";
import { useQueryClient } from "@tanstack/react-query";
import { getManagers, renewSession } from "@/features/auth/oidc";
import { authApi, type ProfilePatch } from "@/features/auth/api/authApi";
import type { Me } from "@/shared/types/auth";
type AuthContextValue = {
  me: Me | null;
  loading: boolean;
  error: unknown;
  reload: () => Promise<Me>;
  updateProfile: (body: ProfilePatch) => Promise<Me>;
};
const AuthContext = createContext<AuthContextValue | null>(null);
export function AuthProvider({ children }: PropsWithChildren) {
  const queryClient = useQueryClient();
  const generation = useRef(0);
  const latestRequest = useRef(0);
  const identity = useRef("");
  const [me, setMe] = useState<Me | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<unknown>(null);
  const reload = useCallback(async () => {
    const requestGeneration = generation.current;
    const requestId = ++latestRequest.current;
    try {
      const profile = await authApi.me();
      if (
        requestGeneration === generation.current &&
        requestId === latestRequest.current
      ) {
        const nextIdentity = `${profile.sub}:${profile.panel}`;
        if (identity.current && identity.current !== nextIdentity)
          queryClient.removeQueries({
            predicate: (query) => query.queryKey[0] !== "landing",
          });
        identity.current = nextIdentity;
        setMe(profile);
        setError(null);
      }
      return profile;
    } catch (failure) {
      if (
        requestGeneration === generation.current &&
        requestId === latestRequest.current
      ) {
        setMe(null);
        setError(
          failure instanceof ApiError && failure.status === 401
            ? null
            : failure,
        );
      }
      throw failure;
    } finally {
      if (
        requestGeneration === generation.current &&
        requestId === latestRequest.current
      )
        setLoading(false);
    }
  }, [queryClient]);
  useEffect(() => {
    let active = true;
    let cleanup = () => {};
    const clear = () => {
      if (active) {
        generation.current++;
        identity.current = "";
        setMe(null);
        setError(null);
        setLoading(false);
        queryClient.removeQueries({
          predicate: (query) => query.queryKey[0] !== "landing",
        });
      }
    };
    const fail = (event: Event) => {
      if (active) {
        generation.current++;
        identity.current = "";
        setError((event as CustomEvent).detail);
        setMe(null);
        setLoading(false);
        queryClient.removeQueries({
          predicate: (query) => query.queryKey[0] !== "landing",
        });
      }
    };
    window.addEventListener("gradian:session-lost", clear);
    window.addEventListener("gradian:account-error", fail);
    void (async () => {
      const { signIn } = await getManagers();
      if (!active) return;
      const loaded = () => {
        if (active) void reload().catch(() => {});
      };
      const renewalError = () => {
        /* Keep a valid token; the next API request renews once if needed. */
      };
      const expired = () => {
        if (active) void renewSession().catch(clear);
      };
      signIn.events.addUserLoaded(loaded);
      signIn.events.addUserUnloaded(clear);
      signIn.events.addUserSignedOut(clear);
      signIn.events.addAccessTokenExpired(expired);
      signIn.events.addSilentRenewError(renewalError);
      cleanup = () => {
        signIn.events.removeUserLoaded(loaded);
        signIn.events.removeUserUnloaded(clear);
        signIn.events.removeUserSignedOut(clear);
        signIn.events.removeAccessTokenExpired(expired);
        signIn.events.removeSilentRenewError(renewalError);
      };
      // Callback owns code exchange; do not start a competing /me request here.
      if (window.location.pathname === "/auth/callback") {
        setLoading(false);
        return;
      }
      const user = await signIn.getUser();
      if (!active) return;
      if (user) await reload();
      else clear();
    })().catch((failure: unknown) => {
      if (active) {
        setError(
          failure instanceof ApiError && failure.status === 401
            ? null
            : failure,
        );
        setLoading(false);
      }
    });
    return () => {
      active = false;
      generation.current++;
      cleanup();
      window.removeEventListener("gradian:session-lost", clear);
      window.removeEventListener("gradian:account-error", fail);
    };
  }, [reload, queryClient]);
  const updateProfile = async (body: ProfilePatch) => {
    const requestGeneration = generation.current;
    const requestId = ++latestRequest.current;
    const profile = await authApi.updateProfile(body);
    if (
      requestGeneration === generation.current &&
      requestId === latestRequest.current
    )
      setMe(profile);
    queryClient.invalidateQueries({ queryKey: ["panel"] });
    return profile;
  };
  return (
    <AuthContext.Provider value={{ me, loading, error, reload, updateProfile }}>
      {children}
    </AuthContext.Provider>
  );
}
export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useAuth must be used inside AuthProvider");
  return value;
}
