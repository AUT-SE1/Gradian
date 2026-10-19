import type { PortalRole } from "./portal";
export type Page<T> = {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
};
export type Countdown = {
  date: string;
  state: "upcoming" | "today" | "past";
  days_remaining: number;
  label: string;
};
export type PanelInfo = {
  panel: PortalRole;
  home_path: string;
  header: {
    full_name: string;
    avatar_url: string;
    consultant_type: "consultant" | "top_ranker" | null;
    field_of_study: string | null;
    field_of_study_label: string | null;
  };
  countdown: Countdown;
};
export type ServiceEntry = {
  key: string;
  title_fa: string;
  title_en: string;
  description: string;
  button_label: string;
  icon: string;
  order: number;
  status: "available" | "unavailable";
  mode: "embed" | "redirect";
  url: string | null;
};
export type Dashboard = {
  welcome: { message: string; tip: string } | null;
  countdown: Countdown;
  study_streak: {
    current_days: number;
    best_days: number;
    message: string;
    week: { day: string; done: boolean }[];
  } | null;
  experience_feed:
    | {
        id: number;
        author: string;
        author_title: string;
        title: string;
        excerpt: string;
        likes: number;
        comments: number;
      }[]
    | null;
};
export type NotificationList = Page<{
  id: number;
  title: string;
  body: string;
  created_at: string;
  is_read: boolean;
}> & { unread_count: number };
type Link = { label: string; href: string };
export type Landing = {
  navbar: {
    brand: string;
    links: Link[];
    login_label: string;
    register_label: string;
  } | null;
  hero: {
    eyebrow: string;
    title: string;
    subtitle: string;
    primary_cta_label: string;
    secondary_cta_label: string;
    image_url: string;
  } | null;
  statistics: { key: string; value: string; label: string }[] | null;
  missions: { title: string; description: string; icon: string }[] | null;
  teachers:
    | { name: string; title: string; bio: string; avatar_url: string }[]
    | null;
  rankers:
    | {
        name: string;
        rank: string;
        field: string;
        quote: string;
        avatar_url: string;
      }[]
    | null;
  testimonials:
    | { name: string; role: string; text: string; avatar_url: string }[]
    | null;
  footer: { description: string; links: Link[]; copyright: string } | null;
};
