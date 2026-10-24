from catalog.sheets import load_contract
from django.http import JsonResponse

API_BODY_LIMIT = 65536
# Export uploads carry a whole CSV: the contract limit plus room for the form fields.
UPLOAD_PATHS = ("/api/private/v1/imports/", "/api/private/v1/imports/diagnose/")
UPLOAD_OVERHEAD = 65536


class APIRequestLimit:
    """Refuses oversized API requests from the declared length, before any body is read."""

    def __init__(self, get_response):
        self.get_response = get_response
        self.upload_limit = load_contract()["input"]["max_bytes"] + UPLOAD_OVERHEAD

    def __call__(self, request):
        if request.path.startswith("/api/"):
            limit = self.upload_limit if request.path in UPLOAD_PATHS else API_BODY_LIMIT
            length = request.headers.get("Content-Length") or "0"
            if (
                not length.isdigit()
                or int(length) > limit
                or len(request.get_full_path().encode()) > API_BODY_LIMIT
            ):
                return JsonResponse({"code": "http_413", "detail": "Request too large"}, status=413)
        return self.get_response(request)
