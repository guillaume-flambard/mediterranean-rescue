import { Collapsible } from "@base-ui/react/collapsible";
import type { ReactNode } from "react";

// Technical details and provenance shown on demand.
export function Disclosure({ title, children, defaultOpen = false }: { title: string; children: ReactNode; defaultOpen?: boolean }) {
  return (
    <Collapsible.Root defaultOpen={defaultOpen} className="ui-disclosure">
      <Collapsible.Trigger className="ui-disclosure__trigger">
        <span aria-hidden className="ui-disclosure__chevron">
          ›
        </span>
        {title}
      </Collapsible.Trigger>
      <Collapsible.Panel className="ui-disclosure__panel">{children}</Collapsible.Panel>
    </Collapsible.Root>
  );
}
