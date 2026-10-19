import { expect, it } from "vitest";
import { serviceUrl } from "@/features/portal/api/portalApi";
import type { ServiceEntry } from "@/shared/types/content";
const entry = {
  status: "available",
  url: "http://localhost:8003/app",
  mode: "redirect",
} as ServiceEntry;
it("opens an available group service without adding tokens", () => {
  expect(serviceUrl(entry)).toBe(entry.url);
});
it("does not link an unavailable service or unsafe scheme", () => {
  expect(serviceUrl({ ...entry, status: "unavailable" })).toBeNull();
  expect(serviceUrl({ ...entry, url: "javascript:alert(1)" })).toBeNull();
  expect(serviceUrl({ ...entry, url: null })).toBeNull();
});
