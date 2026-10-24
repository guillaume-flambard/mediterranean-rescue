from catalog.schema import schema
from django.conf import settings
from django.contrib import admin
from django.db import connection
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.urls import path
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_GET
from strawberry.django.views import GraphQLView


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
    path(
        "graphql/",
        csrf_protect(
            GraphQLView.as_view(
                schema=schema,
                graphql_ide="graphiql" if settings.DEBUG else None,
                allow_queries_via_get=True,
            )
        ),
    ),
]
