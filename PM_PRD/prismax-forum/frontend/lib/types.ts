export interface User {
  id: number;
  name: string;
  initials: string;
  email?: string | null;
  avatar_color?: string | null;
}

export type BlockType = "p" | "h2" | "quote" | "bullet" | "code" | "divider" | "image";

export interface Block {
  type: BlockType;
  html?: string;
  text?: string;
  caption?: string;
  src?: string | null;
}

export interface ThreadCard {
  id: number;
  title: string;
  excerpt: string;
  category: string;
  cover_image?: string | null;
  author: User;
  accent: boolean;
  badge?: string | null;
  status: string;
  date: string;
  created_at: string;
  comment_count: number;
  like_count: number;
  liked: boolean;
  saved: boolean;
}

export interface ThreadDetail extends ThreadCard {
  content: Block[];
}

export interface ThreadList {
  items: ThreadCard[];
  total: number;
}

export interface Comment {
  id: number;
  body: string;
  author: User;
  parent_id?: number | null;
  created_at: string;
  time: string;
  like_count: number;
  liked: boolean;
  replies: Comment[];
}

export interface Category {
  label: string;
  count: number;
}

export interface ToggleResult {
  active: boolean;
  count: number;
}

export interface PresetUser {
  external_id: string;
  name: string;
  avatar_color?: string;
}
