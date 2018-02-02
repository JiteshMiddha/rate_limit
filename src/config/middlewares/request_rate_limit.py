__author__ = 'sanjeev'

from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth import authenticate
from django.core.cache import cache
from django.utils.cache import patch_vary_headers
from oauth2_provider.models import AccessToken


class RequestRateLimitingMiddleware:
    """
    Middleware for rate limiting requests

    With each request, the client has to sent its client_id.
    1. If client_id is not sent or its not registered with the Service,
    it will not serve the request and raise appropriate error
    2. If client id is registered with the service, the request will be
    checked against the Client's rate limiting policy. If passed, the request will be forwarded
    otherwise client will get rate-limiting exception

    """
    def raise_error(self):
        return self

    def check_policy(self, request):
        print(request)
        return self

    def check_existence(self):
        print(self)
        return True

    def process_request(self, request):
        client_id = request.META.get('HTTP_AUTHORIZATION', '')
        if not client_id:
            return self.raise_error()
        if not self.check_existence():
            raise self.raise_error()
        self.check_policy(request)

    def process_response(self, request, response):
        patch_vary_headers(response, ('Authorization',))
        return response
