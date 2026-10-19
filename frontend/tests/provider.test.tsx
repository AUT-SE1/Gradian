import { act, render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { beforeEach, expect, it, vi } from "vitest";
import { ApiError } from "@/shared/api/ApiError";
const mocks = vi.hoisted(() => ({
  me: vi.fn(),
  getUser: vi.fn(),
  loaded: undefined as undefined | (() => void),
}));
vi.mock("@/features/auth/api/authApi", () => ({ authApi: { me: mocks.me } }));
vi.mock("@/features/auth/oidc", () => ({
  getManagers: async () => ({
    signIn: {
      getUser: mocks.getUser,
      events: {
        addUserLoaded: (callback: () => void) => {
          mocks.loaded = callback;
        },
        removeUserLoaded: vi.fn(),
        addUserUnloaded: vi.fn(),
        removeUserUnloaded: vi.fn(),
        addUserSignedOut: vi.fn(),
        removeUserSignedOut: vi.fn(),
        addAccessTokenExpired: vi.fn(),
        removeAccessTokenExpired: vi.fn(),
        addSilentRenewError: vi.fn(),
        removeSilentRenewError: vi.fn(),
      },
    },
  }),
  renewSession: vi.fn(),
}));
import { AuthProvider, useAuth } from "@/app/providers/AuthProvider";
function Status() {
  const auth = useAuth();
  return (
    <div>
      {auth.loading
        ? "loading"
        : auth.me?.panel || (auth.error ? "error" : "anonymous")}
    </div>
  );
}
function mount() {
  const client = new QueryClient();
  render(
    <QueryClientProvider client={client}>
      <AuthProvider>
        <Status />
      </AuthProvider>
    </QueryClientProvider>,
  );
  return client;
}
beforeEach(() => {
  mocks.getUser.mockResolvedValue({ access_token: "saved" });
  mocks.me.mockResolvedValue({ sub: "same", panel: "student" });
  window.history.replaceState({}, "", "/student");
});
it("restores the backend profile from a persisted OIDC user", async () => {
  mount();
  expect(await screen.findByText("student")).toBeInTheDocument();
});
it("keeps a failed token renewal in the anonymous state", async () => {
  mocks.me.mockRejectedValue(new ApiError(401, {}));
  mount();
  expect(await screen.findByText("anonymous")).toBeInTheDocument();
});
it("clears cached account data when the session ends", async () => {
  const client = mount();
  await screen.findByText("student");
  client.setQueryData(["private"], "old");
  act(() => {
    window.dispatchEvent(new Event("gradian:session-lost"));
  });
  expect(screen.getByText("anonymous")).toBeInTheDocument();
  expect(client.getQueryData(["private"])).toBeUndefined();
});
it("does not restore a profile request that finishes after logout", async () => {
  let resolve!: (value: unknown) => void;
  mocks.me.mockReturnValue(
    new Promise((done) => {
      resolve = done;
    }),
  );
  mount();
  await vi.waitFor(() => expect(mocks.me).toHaveBeenCalled());
  act(() => {
    window.dispatchEvent(new Event("gradian:session-lost"));
  });
  await act(async () => {
    resolve({ sub: "same", panel: "admin" });
  });
  expect(screen.getByText("anonymous")).toBeInTheDocument();
});
it("refreshes the role from /me after a token-loaded event", async () => {
  const client = mount();
  await screen.findByText("student");
  client.setQueryData(["private"], "old");
  mocks.me.mockResolvedValue({ sub: "same", panel: "professor" });
  act(() => mocks.loaded?.());
  expect(await screen.findByText("professor")).toBeInTheDocument();
  expect(client.getQueryData(["private"])).toBeUndefined();
});

it("keeps public landing content cached while clearing an account session", async () => {
  const client = mount();
  await screen.findByText("student");
  client.setQueryData(["landing"], { hero: null });
  act(() => {
    window.dispatchEvent(new Event("gradian:session-lost"));
  });
  expect(client.getQueryData(["landing"])).toEqual({ hero: null });
});
