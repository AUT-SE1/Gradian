import { beforeEach, expect, it, vi } from "vitest";
import { ApiError } from "@/shared/api/ApiError";
const mocks = vi.hoisted(() => ({
  getUser: vi.fn(),
  removeUser: vi.fn(),
  renew: vi.fn(),
  signout: vi.fn(),
}));
vi.mock("@/features/auth/oidc", () => ({
  getManagers: async () => ({
    signIn: {
      getUser: mocks.getUser,
      removeUser: mocks.removeUser,
      signoutRedirect: mocks.signout,
    },
  }),
  renewSession: mocks.renew,
}));
import { api } from "@/shared/api/authedClient";
import { httpClient } from "@/shared/api/httpClient";
beforeEach(() => {
  vi.stubEnv("VITE_API_BASE_URL", "/api/v1");
  mocks.getUser.mockResolvedValue({ access_token: "original", expired: false });
  mocks.removeUser.mockResolvedValue(undefined);
});
it("sends the current bearer token to the versioned endpoint", async () => {
  const fetch = vi
    .fn()
    .mockResolvedValue(
      new Response(JSON.stringify({ panel: "student" }), { status: 200 }),
    );
  vi.stubGlobal("fetch", fetch);
  expect(await api.get("/me")).toEqual({ panel: "student" });
  expect(fetch.mock.calls[0][0]).toMatch(/\/api\/v1\/me$/);
  expect(fetch.mock.calls[0][1].headers.get("Authorization")).toBe(
    "Bearer original",
  );
});
it("renews once on 401 and retries with the new token", async () => {
  const fetch = vi
    .fn()
    .mockResolvedValueOnce(new Response("{}", { status: 401 }))
    .mockResolvedValueOnce(new Response('{"ok":true}', { status: 200 }));
  vi.stubGlobal("fetch", fetch);
  mocks.renew.mockResolvedValue({ access_token: "renewed", expired: false });
  expect(await api.get("/me")).toEqual({ ok: true });
  expect(mocks.renew).toHaveBeenCalledTimes(1);
  expect(fetch.mock.calls[1][1].headers.get("Authorization")).toBe(
    "Bearer renewed",
  );
});
it("does not retry or log out on forbidden panel access", async () => {
  vi.stubGlobal(
    "fetch",
    vi
      .fn()
      .mockResolvedValue(
        new Response(
          '{"code":"permission_denied","message":"forbidden","details":{}}',
          { status: 403 },
        ),
      ),
  );
  await expect(api.get("/student/dashboard")).rejects.toMatchObject({
    status: 403,
  });
  expect(mocks.renew).not.toHaveBeenCalled();
  expect(mocks.removeUser).not.toHaveBeenCalled();
});
it("clears a session when the retry is also unauthorized", async () => {
  const fetch = vi.fn().mockResolvedValue(new Response("{}", { status: 401 }));
  vi.stubGlobal("fetch", fetch);
  mocks.renew.mockResolvedValue({ access_token: "renewed", expired: false });
  const listener = vi.fn();
  window.addEventListener("gradian:session-lost", listener);
  await expect(api.get("/me")).rejects.toBeInstanceOf(ApiError);
  expect(fetch).toHaveBeenCalledTimes(2);
  expect(mocks.renew).toHaveBeenCalledTimes(1);
  expect(listener).toHaveBeenCalledTimes(1);
  expect(mocks.removeUser).toHaveBeenCalledTimes(1);
  window.removeEventListener("gradian:session-lost", listener);
});
it("returns to login if silent renewal fails", async () => {
  mocks.getUser.mockResolvedValue({ access_token: "expired", expired: true });
  mocks.renew.mockRejectedValue(new Error("offline"));
  await expect(api.get("/me")).rejects.toMatchObject({ status: 401 });
  expect(mocks.removeUser).toHaveBeenCalledTimes(1);
});
it("normalizes trailing slashes and leaves public requests unauthenticated", async () => {
  const fetch = vi.fn().mockResolvedValue(new Response("{}", { status: 200 }));
  vi.stubGlobal("fetch", fetch);
  await httpClient.get("/auth/config/");
  expect(fetch.mock.calls[0][0]).toMatch(/\/auth\/config$/);
  expect(fetch.mock.calls[0][1].headers.has("Authorization")).toBe(false);
});
