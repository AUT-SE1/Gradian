import { expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
const auth = vi.hoisted(() => ({
  me: null as null | { panel: string; home_path: string },
  loading: false,
  error: null,
}));
vi.mock("@/app/providers/AuthProvider", () => ({
  useAuth: () => ({ ...auth, reload: vi.fn() }),
}));
vi.mock("@/app/layouts/PortalLayout", async () => {
  const { Outlet } = await import("react-router-dom");
  return { PortalLayout: () => <Outlet /> };
});
vi.mock("@/features/portal/pages/PortalHomePage", () => ({
  PortalHomePage: ({ portal }: { portal: string }) => <div>panel:{portal}</div>,
}));
vi.mock("@/features/landing/pages/LandingPage", () => ({
  LandingPage: () => <div>landing</div>,
}));
vi.mock("@/features/auth/pages/LoginPage", () => ({
  LoginPage: () => <div>login required</div>,
}));
import { AppRouter } from "@/app/router/AppRouter";
function visit(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <AppRouter />
    </MemoryRouter>,
  );
}
it("requires authentication on a direct panel visit", async () => {
  auth.me = null;
  visit("/student");
  expect(await screen.findByText("login required")).toBeInTheDocument();
});
it.each(["student", "consultant", "professor", "admin"])(
  "opens the correct %s panel",
  (panel) => {
    auth.me = { panel, home_path: `/${panel}` };
    visit(`/${panel}`);
    expect(screen.getByText(`panel:${panel}`)).toBeInTheDocument();
  },
);
it("blocks a student from opening the administrator page", () => {
  auth.me = { panel: "student", home_path: "/student" };
  visit("/admin");
  expect(screen.queryByText("panel:admin")).not.toBeInTheDocument();
  expect(screen.getByRole("link")).toHaveAttribute("href", "/student");
});
it("keeps old teacher links compatible with the canonical route", () => {
  auth.me = { panel: "professor", home_path: "/professor" };
  visit("/instructor");
  expect(screen.getByText("panel:professor")).toBeInTheDocument();
});
