from catalog.api import EventsView, EventView, EvidenceView, MapPointsView
from catalog.private_api import (
    ExactCarriesView,
    IdentitiesView,
    MeView,
    ReviewDecisionView,
    ReviewRowsView,
    ReviewRowView,
    SessionView,
    SnapshotsView,
)
from django.contrib import admin
from django.db import connection
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.urls import path
from django.views.decorators.http import require_GET
from drf_spectacular.views import SpectacularAPIView


@require_GET
def csrf(request):
    response = JsonResponse({"csrfToken": get_token(request)})
    response["Cache-Control"] = "no-store"
    return response


@require_GET
def health(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except Exception:
        return JsonResponse({"status": "unavailable"}, status=503)
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/csrf/", csrf),
    path("api/health/", health),
    path("api/v1/events/", EventsView.as_view()),
    path("api/v1/events/<uuid:id>/", EventView.as_view()),
    path("api/v1/events/<uuid:id>/evidence/", EvidenceView.as_view()),
    path("api/v1/map-points/", MapPointsView.as_view()),
    path("api/private/v1/me/", MeView.as_view()),
    path("api/private/v1/session/", SessionView.as_view()),
    path("api/private/v1/snapshots/", SnapshotsView.as_view()),
    path("api/private/v1/review/rows/", ReviewRowsView.as_view()),
    path("api/private/v1/review/rows/<uuid:id>/", ReviewRowView.as_view()),
    path("api/private/v1/review/rows/<uuid:id>/decision/", ReviewDecisionView.as_view()),
    path("api/private/v1/review/snapshots/<uuid:id>/exact-carries/", ExactCarriesView.as_view()),
    path("api/private/v1/review/identities/", IdentitiesView.as_view()),
    path(
        "api/v1/schema/",
        SpectacularAPIView.as_view(authentication_classes=[], permission_classes=[]),
    ),
]
