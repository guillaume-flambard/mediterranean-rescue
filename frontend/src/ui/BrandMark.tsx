import type { SVGProps } from "react";

// The project's own mark, drawn for this site: a documented point above the sea. It is not the
// SOS MEDITERRANEE logo, which belongs to the association and is not used without its consent.
// On the navy bars it is drawn without its tile; the tile version is the favicon and app icon.
export function BrandMark({ tile = false, size = 28, ...props }: { tile?: boolean; size?: number } & SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 64 64" width={size} height={size} aria-hidden="true" focusable="false" {...props}>
      {tile && <rect width="64" height="64" rx="15" fill="#1B2747" />}
      <circle cx="32" cy="23" r="12.5" fill="none" stroke="#E83E1B" strokeOpacity="0.7" strokeWidth="2.5" />
      <circle cx="32" cy="23" r="6.5" fill="#E83E1B" stroke="#FFFFFF" strokeWidth="3" />
      <path d="M10 41c4.4-4 8.6-4 13 0s8.6 4 13 0 8.6-4 13 0 6.6 3.4 9 2" fill="none" stroke="#FFFFFF" strokeWidth="4.2" strokeLinecap="round" />
      <path d="M14 51c3.6-3.2 7-3.2 10.6 0s7 3.2 10.6 0 7-3.2 10.6 0" fill="none" stroke="#FFFFFF" strokeOpacity="0.55" strokeWidth="3.4" strokeLinecap="round" />
    </svg>
  );
}
