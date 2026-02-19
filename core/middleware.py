from django.shortcuts import redirect
from django.conf import settings


class LoginRequiredMiddleware:
    """Middleware to require login for all pages except login and static files."""

    EXEMPT_URLS = [
        "/login/",
        "/api/login/",
        "/static/",
        "/admin/",
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not self._is_exempt(request.path):
            if not request.session.get("user_id"):
                return redirect(settings.LOGIN_URL)
        response = self.get_response(request)
        return response

    def _is_exempt(self, path):
        return any(path.startswith(url) for url in self.EXEMPT_URLS)
