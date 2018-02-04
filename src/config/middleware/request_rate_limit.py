__author__ = 'sanjeev'

from django.core.cache import cache
import json
from django.http import HttpResponse


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

    TOO_MANY_REQUESTS_RESPONSE_CODE = {"code": 429, "message": "Rate limit exceeded"}

    CLIENT_NOT_REGISTERED_RESPONSE_CODE = {"code": 403, "message": "Forbidden"}

    def sliding_window_logic(self):
        """
        MULTI
        ZREMRANGEBYSCORE $accessToken 0 ($now - $slidingWindow)
        ZRANGE $accessToken 0 -1
        ZADD $accessToken $now $now
        EXPIRE $accessToken $slidingWindow
        EXEC
        :return:
        """
        print(self)
        return None

    @classmethod
    def keys(cls):
        client_id = str("CLIENT_1")
        global_key = client_id + ":" + "GLOBAL"
        # HTTP methods: GET / POST / PATCH / PUT / DELETE / OPTIONS / HEAD / CONNECT / TRACE
        client_method_key = client_id + ":" + "GET"
        client_api_key = client_id + ":" + "url"
        """

        # Format is of the following type:
        CLIENT_1:MAX:<specialization>:SEC   expires: 30 (in second)
        where specialization can be :
        1. GLOBAL
        2. METHOD:<method_name>
        3. API: <api url>

        # Sliding Window Algorithm
        CLIENT_1:METHOD:GET:SEC    expires: SEC_val
        CLIENT_1:METHOD:GET:MIN    expires: MIN_val * 60
        CLIENT_1:METHOD:GET:HOUR   expires: HOUR_val * 3600

        # Bucket Algorithm
        CLIENT_1:METHOD:GET:WEEK   expires: WEEK_val * 3600 * 7
        CLIENT_1:METHOD:GET:MONTH  expires: MONTH_val * 3600 * 30
        CLIENT_1:GLOBAL


        CLIENT_1:API:/api/v4/status/:SEC        expires: SEC_val
        CLIENT_1:API:/api/v4/status/:MIN        expires: MIN_val * 60
        CLIENT_1:API:/api/v4/status/:HOUR       expires: HOUR_val * 3600
        CLIENT_1:API:/api/v4/status/:WEEK       expires: WEEK_val * 3600 * 7
        CLIENT_1:API:/api/v4/status/:MONTH      expires: MONTH_val * 3600 * 30

        """

    @classmethod
    def error_response(cls, response_code):
        response = {
            "code": response_code["code"],
            "message": response_code["message"]
        }
        return HttpResponse(json.dumps(response), status=response['code'], content_type="application/json")

    def make_key(key, key_prefix, version):
        return ':'.join([key_prefix, str(version), key])

    def get_from_cache(self, key):
        from django.core.cache import caches
        cache.set('my_key', 'hello, world!', 30)
        cache.get('my_key')
        cache.set_many({'a': 1, 'b': 2, 'c': 3})
        cache.delete_many(['a', 'b', 'c'])
        cache.delete('a')
        cache.get_many(['a', 'b', 'c'])
        cache.clear()
        cache.incr('num')
        cache.decr('num')

    @classmethod
    def get_key_name(cls, client_id, method_name=None, path=None):
        key_name = str(client_id)
        key_name = "{0}:{1}".format(key_name + str(method_name)) if method_name else key_name
        key_name = "{0}:{1}".format(key_name + str(path)) if path else key_name
        return key_name

    def check_existence(self, client_id):
        # Check If client is registered for service
        key = self.get_key_name(client_id)

        print(self)
        return True

    def process_request(self, request):
        # key HTTP_AUTHORIZATION contains the client_key,
        # for authentication / authorization purposes
        client_id = request.META.get('HTTP_AUTHORIZATION', '')
        if not client_id:
            return self.error_response(self.CLIENT_NOT_REGISTERED_RESPONSE_CODE)
        if not self.check_existence(client_id):
            return self.error_response(self.CLIENT_NOT_REGISTERED_RESPONSE_CODE)
        #
        http_method = request.method
        url = request.path
        self.check_policy(client_id, http_method, url)

    @classmethod
    def form_all_keys(cls, client_id, http_method, url):
        # Keys can be in the following form:
        """
        CLIENT_1:MAX:<specialization>:SEC  expires: 30 (in second)
        where specialization can be :
        1. GLOBAL
        2. METHOD:<method_name>
        3. API: <api url>
        """
        global_keys = ["{0}:GLOBAL:{1}".format(client_id, _) for _ in ('SEC', 'MIN', 'HOUR', 'WEEK', 'MONTH')]
        method_spec_keys = ["{0}:METHOD:{1}:{2}".format(client_id, http_method, _) for _ in ('SEC', 'MIN', 'HOUR', 'WEEK', 'MONTH')]
        api_spec_keys = ["{0}:API:{1}:{2}".format(client_id, url, _) for _ in ('SEC', 'MIN', 'HOUR', 'WEEK', 'MONTH')]
        return global_keys, method_spec_keys, api_spec_keys

    @classmethod
    def check_policy(cls, client_id, http_method, url):
        global_keys, method_spec_keys, api_spec_keys = cls.form_all_keys(client_id, http_method, url)
        cache.get_many(global_keys + method_spec_keys + api_spec_keys)

        cache.set('my_key', 'hello, world!', 30)

        # print(request)
        # return self
