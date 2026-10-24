from datetime import date
from enum import Enum
from uuid import UUID

import strawberry
import strawberry_django
from django.conf import settings
from django.contrib.gis.geos import Polygon
from graphql import GraphQLError
from strawberry.extensions import MaxAliasesLimiter, QueryDepthLimiter
from strawberry_django.optimizer import DjangoOptimizerExtension

from .models import Event, Evidence, Port, Source, Vessel, Voyage


@strawberry.enum
class Kind(Enum):
    RESCUE = "rescue"
    TRANSFER = "transfer"
    MEDEVAC = "medevac"
    INCIDENT = "incident"
    SHIPWRECK = "shipwreck"
    DEAD_MISSING = "dead_missing"


@strawberry.type
class Position:
    longitude: float
    latitude: float
    precision: str


@strawberry_django.type(Source, fields=["id", "name", "url", "license_note", "synthetic"])
class SourceType:
    pass


@strawberry_django.type(Vessel, fields=["id", "name", "imo"])
class VesselType:
    pass


@strawberry_django.type(Port, fields=["id", "name", "country_code"])
class PortType:
    pass


@strawberry_django.type(Voyage, fields=["id", "title", "started_on", "ended_on", "logbook_url"])
class VoyageType:
    pass


@strawberry_django.type(Evidence, fields=["id", "label", "url"])
class EvidenceType:
    pass


@strawberry_django.type(
    Event,
    fields=["id", "title", "summary", "occurred_on", "people", "women", "minors", "source_url"],
)
class EventType:
    source: SourceType
    vessel: VesselType | None
    voyage: VoyageType | None
    port: PortType | None
    evidence: list[EvidenceType]

    @strawberry.field
    def kind(self) -> Kind:
        return Kind(self.kind)

    @strawberry.field
    def position(self) -> Position | None:
        if self.location is None:
            return None
        return Position(
            longitude=self.location.x, latitude=self.location.y, precision=self.location_precision
        )


@strawberry.input
class Bounds:
    west: float
    south: float
    east: float
    north: float


@strawberry.input
class EventFilter:
    start: date | None = None
    end: date | None = None
    kind: Kind | None = None
    bounds: Bounds | None = None


def filtered_events(filters: EventFilter | None):
    queryset = Event.objects.public()
    if not filters:
        return queryset
    if filters.start and filters.end and filters.start > filters.end:
        raise GraphQLError("Start date must not exceed end date")
    if filters.start:
        queryset = queryset.filter(occurred_on__gte=filters.start)
    if filters.end:
        queryset = queryset.filter(occurred_on__lte=filters.end)
    if filters.kind:
        queryset = queryset.filter(kind=filters.kind.value)
    if filters.bounds:
        b = filters.bounds
        if not (-180 <= b.west < b.east <= 180 and -90 <= b.south < b.north <= 90):
            raise GraphQLError("Invalid geographic bounds")
        queryset = queryset.filter(
            location__intersects=Polygon.from_bbox((b.west, b.south, b.east, b.north))
        )
    return queryset


@strawberry.type
class EventPage:
    items: list[EventType]
    total_count: int
    has_next: bool


@strawberry.type
class MapPoint:
    id: strawberry.ID
    longitude: float
    latitude: float
    kind: Kind


@strawberry.type
class MapResult:
    points: list[MapPoint]
    located_count: int
    truncated: bool


@strawberry.type
class Query:
    @strawberry.field
    def data_mode(self) -> str:
        return settings.DATA_MODE

    @strawberry.field
    def events(
        self, filters: EventFilter | None = None, limit: int = 50, offset: int = 0
    ) -> EventPage:
        if not 1 <= limit <= 100 or not 0 <= offset <= 100000:
            raise GraphQLError("Use limit 1..100 and offset 0..100000")
        queryset = (
            filtered_events(filters)
            .select_related("source", "vessel", "voyage", "port")
            .prefetch_related("evidence")
        )
        count = queryset.count()
        return EventPage(
            items=list(queryset[offset : offset + limit]),
            total_count=count,
            has_next=offset + limit < count,
        )

    @strawberry.field
    def event(self, id: UUID) -> EventType | None:
        return (
            Event.objects.public()
            .select_related("source", "vessel", "voyage", "port")
            .prefetch_related("evidence")
            .filter(pk=id)
            .first()
        )

    @strawberry.field
    def map_points(self, filters: EventFilter | None = None) -> MapResult:
        queryset = filtered_events(filters).exclude(location=None)
        count = queryset.count()
        points = [
            MapPoint(
                id=strawberry.ID(str(event.id)),
                longitude=event.location.x,
                latitude=event.location.y,
                kind=Kind(event.kind),
            )
            for event in queryset.only("id", "location", "kind", "occurred_on")[:2000]
        ]
        return MapResult(points=points, located_count=count, truncated=count > 2000)


schema = strawberry.Schema(
    query=Query,
    extensions=[
        DjangoOptimizerExtension,
        QueryDepthLimiter(max_depth=8),
        MaxAliasesLimiter(max_alias_count=10),
    ],
)
