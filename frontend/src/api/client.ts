import createFetchClient from "openapi-fetch";
import createClient from "openapi-react-query";
import type { paths, components } from "./schema";
export const api = createClient(createFetchClient<paths>({ baseUrl: "", credentials: "same-origin" }));
export type Kind = components["schemas"]["KindEnum"];
export type EventFilter = NonNullable<paths["/api/v1/map-points/"]["get"]["parameters"]["query"]>;
export type MapPoints = components["schemas"]["MapResult"]["points"];
