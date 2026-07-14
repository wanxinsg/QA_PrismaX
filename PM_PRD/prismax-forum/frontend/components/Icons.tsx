import type { CSSProperties } from "react";

interface IconProps {
  size?: number;
  fill?: string;
  style?: CSSProperties;
}

const base = (size: number) => ({
  width: size,
  height: size,
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 2,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
});

export const ChatIcon = ({ size = 14 }: IconProps) => (
  <svg {...base(size)}>
    <path d="M21 11.5a8.4 8.4 0 0 1-8.5 8.5 8.5 8.5 0 0 1-3.8-.9L3 21l1.9-5.7a8.5 8.5 0 1 1 16.1-3.8z" />
  </svg>
);

export const HeartIcon = ({ size = 14, fill = "none" }: IconProps) => (
  <svg {...base(size)} fill={fill}>
    <path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1-1.1a5.5 5.5 0 1 0-7.8 7.8L12 21l8.8-8.6a5.5 5.5 0 0 0 0-7.8z" />
  </svg>
);

export const BookmarkIcon = ({ size = 14, fill = "none" }: IconProps) => (
  <svg {...base(size)} fill={fill}>
    <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z" />
  </svg>
);

export const SearchIcon = ({ size = 17 }: IconProps) => (
  <svg {...base(size)}>
    <circle cx="11" cy="11" r="7" />
    <path d="M21 21l-4.3-4.3" />
  </svg>
);

export const ShareIcon = ({ size = 17 }: IconProps) => (
  <svg {...base(size)}>
    <circle cx="18" cy="5" r="3" />
    <circle cx="6" cy="12" r="3" />
    <circle cx="18" cy="19" r="3" />
    <path d="M8.6 13.5l6.8 4M15.4 6.5l-6.8 4" />
  </svg>
);

export const ArrowLeftIcon = ({ size = 15 }: IconProps) => (
  <svg {...base(size)}>
    <path d="M19 12H5M11 18l-6-6 6-6" />
  </svg>
);

export const PlusIcon = ({ size = 15 }: IconProps) => (
  <svg {...base(size)}>
    <path d="M12 5v14M5 12h14" />
  </svg>
);

export const CloseIcon = ({ size = 14 }: IconProps) => (
  <svg {...base(size)}>
    <path d="M18 6L6 18M6 6l12 12" />
  </svg>
);

export const ImageIcon = ({ size = 17 }: IconProps) => (
  <svg {...base(size)}>
    <rect x="3" y="3" width="18" height="18" rx="2" />
    <circle cx="8.5" cy="8.5" r="1.5" />
    <path d="M21 15l-5-5L5 21" />
  </svg>
);

export const MenuIcon = ({ size = 22, open = false }: IconProps & { open?: boolean }) => (
  <svg {...base(size)}>
    <path d={open ? "M6 6l12 12M6 18L18 6" : "M4 7h16M4 12h16M4 17h16"} />
  </svg>
);
