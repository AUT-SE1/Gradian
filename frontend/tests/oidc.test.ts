import { beforeEach, expect, it, vi } from "vitest";
const state = vi.hoisted(() => ({
  instances: [] as unknown[],
  config: vi.fn(),
  callback: vi.fn(),
  renew: vi.fn(),
}));
vi.mock("@/shared/api/httpClient", () => ({
  httpClient: { get: state.config },
}));
vi.mock("oidc-client-ts", () => ({
  WebStorageStateStore: class {},
  UserManager: class {
    metadataService = {
      getMetadata: async () => ({
        authorization_endpoint: "http://localhost:8080/auth",
      }),
    };
    signinRedirectCallback = state.callback;
    signinSilent = state.renew;
    constructor(settings: unknown) {
      state.instances.push(settings);
    }
  },
}));
beforeEach(() => {
  vi.resetModules();
  state.instances = [];
  state.config.mockResolvedValue({
    issuer: "http://localhost:8080/realms/gradian",
    client_id: "gradian-web",
    landing_url: "http://localhost:5173/",
    registration_endpoint: "http://localhost:8080/register",
  });
});
it("caches auth config and uses the registered callback and registration endpoint", async () => {
  const { getManagers } = await import("@/features/auth/oidc");
  await Promise.all([getManagers(), getManagers()]);
  expect(state.config).toHaveBeenCalledTimes(1);
  expect(state.config).toHaveBeenCalledWith("/auth/config");
  expect(state.instances[0]).toMatchObject({
    client_id: "gradian-web",
    response_type: "code",
    redirect_uri: `${window.location.origin}/auth/callback`,
    automaticSilentRenew: true,
  });
  expect(state.instances[1]).toMatchObject({
    metadata: { authorization_endpoint: "http://localhost:8080/register" },
  });
});
it("exchanges the authorization code only once for repeated callback invocations", async () => {
  state.callback.mockResolvedValue({ access_token: "token" });
  const { finishSignIn } = await import("@/features/auth/oidc");
  await Promise.all([finishSignIn(), finishSignIn()]);
  expect(state.callback).toHaveBeenCalledTimes(1);
});
it("does not cache a failed auth config request", async () => {
  state.config.mockRejectedValueOnce(new Error("offline"));
  const { getManagers } = await import("@/features/auth/oidc");
  await expect(getManagers()).rejects.toThrow("offline");
  await getManagers();
  expect(state.config).toHaveBeenCalledTimes(2);
});
it("shares one silent renewal across simultaneous API failures", async () => {
  let resolve!: (value: unknown) => void;
  state.renew.mockReturnValue(
    new Promise((done) => {
      resolve = done;
    }),
  );
  const { renewSession } = await import("@/features/auth/oidc");
  const first = renewSession();
  const second = renewSession();
  await vi.waitFor(() => expect(state.renew).toHaveBeenCalledTimes(1));
  resolve({ access_token: "new" });
  await Promise.all([first, second]);
});
