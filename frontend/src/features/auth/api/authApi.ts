import { api } from "@/shared/api/authedClient";
import type { Me } from "@/shared/types/auth";
export type ProfilePatch = Partial<
  Pick<
    Me,
    | "email"
    | "first_name"
    | "last_name"
    | "field_of_study"
    | "avatar_url"
    | "bio"
  >
>;
export const authApi = {
  me: () => api.get<Me>("/me"),
  updateProfile: (body: ProfilePatch) => api.patch<Me>("/me", body),
};
