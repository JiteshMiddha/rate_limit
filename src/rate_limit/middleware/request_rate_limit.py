__author__ = 'sanjeev'

import json
from django.http import HttpResponse
from rate_limit.middleware.rate_limit_policy import RateLimitPolicy


class RequestRateLimitingMiddleware:
    """
    Middleware for rate limiting requests from client

    With each request, the client has to sent its client_id.
    1. If client_id is not sent or its not registered with the Service,
        the request will not move forward and appropriate response will be sent to client.
    2. If client id is registered with the service, the request will be
        checked against the Client's rate limiting policy. If passed, the request will be forwarded
        otherwise client will get rate-limiting exception
    """

    TOO_MANY_REQUESTS_RESPONSE_CODE = {"code": 429, "message": "Rate limit exceeded"}

    CLIENT_NOT_REGISTERED_RESPONSE_CODE = {"code": 403, "message": "Forbidden"}

    @classmethod
    def error_response(cls, response_code):
        response = {
            "code": response_code["code"],
            "message": response_code["message"]
        }
        return HttpResponse(json.dumps(response), status=response['code'], content_type="application/json")

    def process_request(self, request):
        # key HTTP_AUTHORIZATION contains the client_key,
        # for authentication / authorization purposes
        client_id = request.META.get('HTTP_AUTHORIZATION', '')
        if not client_id:
            return self.error_response(self.CLIENT_NOT_REGISTERED_RESPONSE_CODE)
        policy = RateLimitPolicy()
        client_id = client_id.upper()
        if not policy.check_policy_exists(client_id):
            return self.error_response(self.CLIENT_NOT_REGISTERED_RESPONSE_CODE)
        #
        http_method = request.method.upper()
        url = request.path.upper()
        limit_reached = policy.check_policy(client_id, http_method, url)
        if limit_reached:
            return self.error_response(self.TOO_MANY_REQUESTS_RESPONSE_CODE)
