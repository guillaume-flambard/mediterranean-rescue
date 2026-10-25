import type { SVGProps } from "react";

// A small authored icon set on one 24px grid with one stroke weight, so every glyph matches.
const PATHS = {
  search: <><circle cx="11" cy="11" r="6.5" /><path d="m16 16 4.5 4.5" /></>,
  close: <path d="M6 6l12 12M18 6 6 18" />,
  chevronDown: <path d="m6 9 6 6 6-6" />,
  calendar: <><rect x="3.5" y="5" width="17" height="15.5" rx="2.5" /><path d="M3.5 10h17M8 3v4M16 3v4" /></>,
  people: <><circle cx="9" cy="8" r="3.2" /><path d="M3 20c.6-3.6 3-5.6 6-5.6s5.4 2 6 5.6" /><path d="M16 5.2a3 3 0 0 1 0 5.6M18 14.6c1.7.7 2.7 2.6 3 5.4" /></>,
  anchor: <><circle cx="12" cy="5" r="2" /><path d="M12 7v13M8 11h8M4.5 13a7.5 7.5 0 0 0 15 0" /></>,
  pin: <><path d="M12 21s-6.5-5.6-6.5-11a6.5 6.5 0 0 1 13 0c0 5.4-6.5 11-6.5 11Z" /><circle cx="12" cy="10" r="2.3" /></>,
  map: <><path d="M9 4 3.5 6v14L9 18l6 2 5.5-2V4L15 6 9 4Z" /><path d="M9 4v14M15 6v14" /></>,
  external: <><path d="M14 4h6v6M20 4l-9 9" /><path d="M18 14v4.5A1.5 1.5 0 0 1 16.5 20h-11A1.5 1.5 0 0 1 4 18.5v-11A1.5 1.5 0 0 1 5.5 6H10" /></>,
  lock: <><rect x="5" y="10.5" width="14" height="10" rx="2.5" /><path d="M8.5 10.5V8a3.5 3.5 0 0 1 7 0v2.5" /></>,
  check: <path d="m5 12.5 4.5 4.5L19 7.5" />,
  alert: <><path d="M12 4 2.8 19.5h18.4L12 4Z" /><path d="M12 10v4.5M12 17.2v.3" /></>,
  arrowRight: <path d="M5 12h14M13 6l6 6-6 6" />,
  info: <><circle cx="12" cy="12" r="8.5" /><path d="M12 11v5.5M12 7.6v.3" /></>,
  help: <><circle cx="12" cy="12" r="8.5" /><path d="M9.6 9.4a2.5 2.5 0 0 1 4.8.9c0 1.7-2.4 2.1-2.4 3.7M12 16.9v.3" /></>,
  grid: <><rect x="4" y="4" width="6.5" height="6.5" rx="1.5" /><rect x="13.5" y="4" width="6.5" height="6.5" rx="1.5" /><rect x="4" y="13.5" width="6.5" height="6.5" rx="1.5" /><rect x="13.5" y="13.5" width="6.5" height="6.5" rx="1.5" /></>,
  listCheck: <><path d="m4 6.5 1.6 1.6L8.5 5M4 15.5l1.6 1.6 2.9-3.1" /><path d="M11.5 7h8.5M11.5 16h8.5" /></>,
  send: <><path d="M20.5 3.5 10 14" /><path d="M20.5 3.5 14 20.5l-4-6.5-6.5-4 17-6.5Z" /></>,
  database: <><ellipse cx="12" cy="6" rx="7.5" ry="2.8" /><path d="M4.5 6v12c0 1.5 3.4 2.8 7.5 2.8s7.5-1.3 7.5-2.8V6" /><path d="M4.5 12c0 1.5 3.4 2.8 7.5 2.8s7.5-1.3 7.5-2.8" /></>,
  upload: <><path d="M12 15V4M7 9l5-5 5 5" /><path d="M5 19.5h14" /></>,
  school: <><path d="M12 5 2.5 9.5 12 14l9.5-4.5L12 5Z" /><path d="M6.5 11.5v4.5c1.5 1.4 3.4 2 5.5 2s4-.6 5.5-2v-4.5M21.5 9.5V15" /></>,
  expand: <><path d="M14 4h6v6M10 20H4v-6" /><path d="m20 4-6.5 6.5M4 20l6.5-6.5" /></>,
  link: <><path d="M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7L11.5 6.8" /><path d="M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1.5-1.5" /></>,
  download: <><path d="M12 4v11M7 10l5 5 5-5" /><path d="M5 19.5h14" /></>,
  signOut: <><path d="M14 4h4.5A1.5 1.5 0 0 1 20 5.5v13a1.5 1.5 0 0 1-1.5 1.5H14" /><path d="M10 8l-4 4 4 4M6 12h10" /></>,
} as const;

export type IconName = keyof typeof PATHS;

export function Icon({ name, size = 20, ...props }: { name: IconName; size?: number } & SVGProps<SVGSVGElement>) {
  return (
    <svg
      viewBox="0 0 24 24"
      width={size}
      height={size}
      fill="none"
      stroke="currentColor"
      strokeWidth={1.75}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
      {...props}
    >
      {PATHS[name]}
    </svg>
  );
}
