import { Tabs as BaseTabs } from "@base-ui/react/tabs";
import type { ReactNode } from "react";

export interface TabItem<V extends string> {
  value: V;
  label: string;
  content: ReactNode;
}

// Sibling views of the same object, never the steps of a form.
export function Tabs<V extends string>({ items, defaultValue, label }: { items: readonly TabItem<V>[]; defaultValue: V; label: string }) {
  return (
    <BaseTabs.Root defaultValue={defaultValue} className="ui-tabs">
      <BaseTabs.List className="ui-tabs__list" aria-label={label}>
        {items.map((item) => (
          <BaseTabs.Tab key={item.value} value={item.value} className="ui-tabs__tab">
            {item.label}
          </BaseTabs.Tab>
        ))}
        <BaseTabs.Indicator className="ui-tabs__indicator" />
      </BaseTabs.List>
      {items.map((item) => (
        <BaseTabs.Panel key={item.value} value={item.value} className="ui-tabs__panel">
          {item.content}
        </BaseTabs.Panel>
      ))}
    </BaseTabs.Root>
  );
}
