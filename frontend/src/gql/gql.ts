/* eslint-disable */
import * as types from './graphql';
import type { TypedDocumentNode as DocumentNode } from '@graphql-typed-document-node/core';

/**
 * Map of all GraphQL operations in the project.
 *
 * This map has several performance disadvantages:
 * 1. It is not tree-shakeable, so it will include all operations in the project.
 * 2. It is not minifiable, so the string of a GraphQL query will be multiple times inside the bundle.
 * 3. It does not support dead code elimination, so it will add unused operations.
 *
 * Therefore it is highly recommended to use the babel or swc plugin for production.
 * Learn more about it here: https://the-guild.dev/graphql/codegen/plugins/presets/preset-client#reducing-bundle-size
 */
type Documents = {
    "query Explore($filters: EventFilter, $offset: Int!) {\n  dataMode\n  events(filters: $filters, limit: 25, offset: $offset) {\n    totalCount\n    hasNext\n    items {\n      id\n      title\n      occurredOn\n      kind\n      people\n      position {\n        longitude\n        latitude\n        precision\n      }\n      vessel {\n        name\n      }\n      source {\n        name\n        synthetic\n      }\n    }\n  }\n  mapPoints(filters: $filters) {\n    locatedCount\n    truncated\n    points {\n      id\n      longitude\n      latitude\n      kind\n    }\n  }\n}\n\nquery EventDetail($id: UUID!) {\n  event(id: $id) {\n    id\n    title\n    summary\n    occurredOn\n    kind\n    people\n    women\n    minors\n    sourceUrl\n    position {\n      longitude\n      latitude\n      precision\n    }\n    source {\n      name\n      url\n      licenseNote\n      synthetic\n    }\n    vessel {\n      name\n      imo\n    }\n    voyage {\n      title\n      startedOn\n      endedOn\n      logbookUrl\n    }\n    port {\n      name\n      countryCode\n    }\n    evidence {\n      label\n      url\n    }\n  }\n}": typeof types.ExploreDocument,
};
const documents: Documents = {
    "query Explore($filters: EventFilter, $offset: Int!) {\n  dataMode\n  events(filters: $filters, limit: 25, offset: $offset) {\n    totalCount\n    hasNext\n    items {\n      id\n      title\n      occurredOn\n      kind\n      people\n      position {\n        longitude\n        latitude\n        precision\n      }\n      vessel {\n        name\n      }\n      source {\n        name\n        synthetic\n      }\n    }\n  }\n  mapPoints(filters: $filters) {\n    locatedCount\n    truncated\n    points {\n      id\n      longitude\n      latitude\n      kind\n    }\n  }\n}\n\nquery EventDetail($id: UUID!) {\n  event(id: $id) {\n    id\n    title\n    summary\n    occurredOn\n    kind\n    people\n    women\n    minors\n    sourceUrl\n    position {\n      longitude\n      latitude\n      precision\n    }\n    source {\n      name\n      url\n      licenseNote\n      synthetic\n    }\n    vessel {\n      name\n      imo\n    }\n    voyage {\n      title\n      startedOn\n      endedOn\n      logbookUrl\n    }\n    port {\n      name\n      countryCode\n    }\n    evidence {\n      label\n      url\n    }\n  }\n}": types.ExploreDocument,
};

/**
 * The graphql function is used to parse GraphQL queries into a document that can be used by GraphQL clients.
 *
 *
 * @example
 * ```ts
 * const query = graphql(`query GetUser($id: ID!) { user(id: $id) { name } }`);
 * ```
 *
 * The query argument is unknown!
 * Please regenerate the types.
 */
export function graphql(source: string): unknown;

/**
 * The graphql function is used to parse GraphQL queries into a document that can be used by GraphQL clients.
 */
export function graphql(source: "query Explore($filters: EventFilter, $offset: Int!) {\n  dataMode\n  events(filters: $filters, limit: 25, offset: $offset) {\n    totalCount\n    hasNext\n    items {\n      id\n      title\n      occurredOn\n      kind\n      people\n      position {\n        longitude\n        latitude\n        precision\n      }\n      vessel {\n        name\n      }\n      source {\n        name\n        synthetic\n      }\n    }\n  }\n  mapPoints(filters: $filters) {\n    locatedCount\n    truncated\n    points {\n      id\n      longitude\n      latitude\n      kind\n    }\n  }\n}\n\nquery EventDetail($id: UUID!) {\n  event(id: $id) {\n    id\n    title\n    summary\n    occurredOn\n    kind\n    people\n    women\n    minors\n    sourceUrl\n    position {\n      longitude\n      latitude\n      precision\n    }\n    source {\n      name\n      url\n      licenseNote\n      synthetic\n    }\n    vessel {\n      name\n      imo\n    }\n    voyage {\n      title\n      startedOn\n      endedOn\n      logbookUrl\n    }\n    port {\n      name\n      countryCode\n    }\n    evidence {\n      label\n      url\n    }\n  }\n}"): (typeof documents)["query Explore($filters: EventFilter, $offset: Int!) {\n  dataMode\n  events(filters: $filters, limit: 25, offset: $offset) {\n    totalCount\n    hasNext\n    items {\n      id\n      title\n      occurredOn\n      kind\n      people\n      position {\n        longitude\n        latitude\n        precision\n      }\n      vessel {\n        name\n      }\n      source {\n        name\n        synthetic\n      }\n    }\n  }\n  mapPoints(filters: $filters) {\n    locatedCount\n    truncated\n    points {\n      id\n      longitude\n      latitude\n      kind\n    }\n  }\n}\n\nquery EventDetail($id: UUID!) {\n  event(id: $id) {\n    id\n    title\n    summary\n    occurredOn\n    kind\n    people\n    women\n    minors\n    sourceUrl\n    position {\n      longitude\n      latitude\n      precision\n    }\n    source {\n      name\n      url\n      licenseNote\n      synthetic\n    }\n    vessel {\n      name\n      imo\n    }\n    voyage {\n      title\n      startedOn\n      endedOn\n      logbookUrl\n    }\n    port {\n      name\n      countryCode\n    }\n    evidence {\n      label\n      url\n    }\n  }\n}"];

export function graphql(source: string) {
  return (documents as any)[source] ?? {};
}

export type DocumentType<TDocumentNode extends DocumentNode<any, any>> = TDocumentNode extends DocumentNode<  infer TType,  any>  ? TType  : never;