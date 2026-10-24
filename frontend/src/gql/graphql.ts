/* eslint-disable */
/** Internal type. DO NOT USE DIRECTLY. */
type Exact<T extends { [key: string]: unknown }> = { [K in keyof T]: T[K] };
/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> = T | { [P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never };
import type { TypedDocumentNode as DocumentNode } from '@graphql-typed-document-node/core';
export type Bounds = {
  readonly east: number;
  readonly north: number;
  readonly south: number;
  readonly west: number;
};

export type EventFilter = {
  readonly bounds?: Bounds | null | undefined;
  readonly end?: string | null | undefined;
  readonly kind?: Kind | null | undefined;
  readonly start?: string | null | undefined;
};

export type Kind =
  | 'DEAD_MISSING'
  | 'INCIDENT'
  | 'MEDEVAC'
  | 'RESCUE'
  | 'SHIPWRECK'
  | 'TRANSFER';

export type ExploreQueryVariables = Exact<{
  filters?: EventFilter | null | undefined;
  offset: number;
}>;


export type ExploreQuery = { readonly dataMode: string, readonly events: { readonly totalCount: number, readonly hasNext: boolean, readonly items: ReadonlyArray<{ readonly id: string, readonly title: string, readonly occurredOn: string, readonly kind: Kind, readonly people: number | null, readonly position: { readonly longitude: number, readonly latitude: number, readonly precision: string } | null, readonly vessel: { readonly name: string } | null, readonly source: { readonly name: string, readonly synthetic: boolean } }> }, readonly mapPoints: { readonly locatedCount: number, readonly truncated: boolean, readonly points: ReadonlyArray<{ readonly id: string, readonly longitude: number, readonly latitude: number, readonly kind: Kind }> } };

export type EventDetailQueryVariables = Exact<{
  id: string;
}>;


export type EventDetailQuery = { readonly event: { readonly id: string, readonly title: string, readonly summary: string, readonly occurredOn: string, readonly kind: Kind, readonly people: number | null, readonly women: number | null, readonly minors: number | null, readonly sourceUrl: string, readonly position: { readonly longitude: number, readonly latitude: number, readonly precision: string } | null, readonly source: { readonly name: string, readonly url: string, readonly licenseNote: string, readonly synthetic: boolean }, readonly vessel: { readonly name: string, readonly imo: string } | null, readonly voyage: { readonly title: string, readonly startedOn: string, readonly endedOn: string | null, readonly logbookUrl: string } | null, readonly port: { readonly name: string, readonly countryCode: string } | null, readonly evidence: ReadonlyArray<{ readonly label: string, readonly url: string }> } | null };


export const ExploreDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"Explore"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"filters"}},"type":{"kind":"NamedType","name":{"kind":"Name","value":"EventFilter"}}},{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"offset"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"Int"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"dataMode"}},{"kind":"Field","name":{"kind":"Name","value":"events"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"filters"},"value":{"kind":"Variable","name":{"kind":"Name","value":"filters"}}},{"kind":"Argument","name":{"kind":"Name","value":"limit"},"value":{"kind":"IntValue","value":"25"}},{"kind":"Argument","name":{"kind":"Name","value":"offset"},"value":{"kind":"Variable","name":{"kind":"Name","value":"offset"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"totalCount"}},{"kind":"Field","name":{"kind":"Name","value":"hasNext"}},{"kind":"Field","name":{"kind":"Name","value":"items"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"title"}},{"kind":"Field","name":{"kind":"Name","value":"occurredOn"}},{"kind":"Field","name":{"kind":"Name","value":"kind"}},{"kind":"Field","name":{"kind":"Name","value":"people"}},{"kind":"Field","name":{"kind":"Name","value":"position"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"longitude"}},{"kind":"Field","name":{"kind":"Name","value":"latitude"}},{"kind":"Field","name":{"kind":"Name","value":"precision"}}]}},{"kind":"Field","name":{"kind":"Name","value":"vessel"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"name"}}]}},{"kind":"Field","name":{"kind":"Name","value":"source"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"name"}},{"kind":"Field","name":{"kind":"Name","value":"synthetic"}}]}}]}}]}},{"kind":"Field","name":{"kind":"Name","value":"mapPoints"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"filters"},"value":{"kind":"Variable","name":{"kind":"Name","value":"filters"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"locatedCount"}},{"kind":"Field","name":{"kind":"Name","value":"truncated"}},{"kind":"Field","name":{"kind":"Name","value":"points"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"longitude"}},{"kind":"Field","name":{"kind":"Name","value":"latitude"}},{"kind":"Field","name":{"kind":"Name","value":"kind"}}]}}]}}]}}]} as unknown as DocumentNode<ExploreQuery, ExploreQueryVariables>;
export const EventDetailDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"EventDetail"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"id"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"UUID"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"event"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"id"},"value":{"kind":"Variable","name":{"kind":"Name","value":"id"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"title"}},{"kind":"Field","name":{"kind":"Name","value":"summary"}},{"kind":"Field","name":{"kind":"Name","value":"occurredOn"}},{"kind":"Field","name":{"kind":"Name","value":"kind"}},{"kind":"Field","name":{"kind":"Name","value":"people"}},{"kind":"Field","name":{"kind":"Name","value":"women"}},{"kind":"Field","name":{"kind":"Name","value":"minors"}},{"kind":"Field","name":{"kind":"Name","value":"sourceUrl"}},{"kind":"Field","name":{"kind":"Name","value":"position"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"longitude"}},{"kind":"Field","name":{"kind":"Name","value":"latitude"}},{"kind":"Field","name":{"kind":"Name","value":"precision"}}]}},{"kind":"Field","name":{"kind":"Name","value":"source"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"name"}},{"kind":"Field","name":{"kind":"Name","value":"url"}},{"kind":"Field","name":{"kind":"Name","value":"licenseNote"}},{"kind":"Field","name":{"kind":"Name","value":"synthetic"}}]}},{"kind":"Field","name":{"kind":"Name","value":"vessel"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"name"}},{"kind":"Field","name":{"kind":"Name","value":"imo"}}]}},{"kind":"Field","name":{"kind":"Name","value":"voyage"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"title"}},{"kind":"Field","name":{"kind":"Name","value":"startedOn"}},{"kind":"Field","name":{"kind":"Name","value":"endedOn"}},{"kind":"Field","name":{"kind":"Name","value":"logbookUrl"}}]}},{"kind":"Field","name":{"kind":"Name","value":"port"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"name"}},{"kind":"Field","name":{"kind":"Name","value":"countryCode"}}]}},{"kind":"Field","name":{"kind":"Name","value":"evidence"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"label"}},{"kind":"Field","name":{"kind":"Name","value":"url"}}]}}]}}]}}]} as unknown as DocumentNode<EventDetailQuery, EventDetailQueryVariables>;