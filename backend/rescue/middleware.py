from django.http import JsonResponse


class GraphQLRequestLimit:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path == "/graphql/":
            length = request.headers.get("Content-Length") or "0"
            if (
                not length.isdigit()
                or int(length) > 65536
                or len(request.get_full_path().encode()) > 65536
            ):
                return JsonResponse({"error": "Request too large"}, status=413)
        return self.get_response(request)
