import type { PortalRole } from "./portal";
export type AuthConfig = {
  issuer: string;
  realm: string;
  client_id: string;
  registration_endpoint: string;
  end_session_url: string;
  landing_url: string;
};
export type Me = {
  sub: string;
  mobile: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  role: PortalRole;
  panel: PortalRole;
  home_path: string;
  consultant_type: "" | "consultant" | "top_ranker";
  field_of_study: "" | "experimental" | "mathematics" | "humanities";
  avatar_url: string;
  bio: string;
};
export type ApiErrorBody = {
  code: string;
  message: string;
  details: Record<string, unknown>;
};
