__author__ = 'sanjeev'

from datetime import datetime
from django.conf import settings
import redis


class RateLimitPolicy:

    MICRO_SECONDS = 1000000

    MEASURE_UNIT = ['SEC', 'MIN', 'HOUR', 'WEEK', 'MONTH']

    MICRO_SEC_COUNT = {"SEC": MICRO_SECONDS,
                       "MIN": MICRO_SECONDS * 60,
                       "HOUR": MICRO_SECONDS * 3600,
                       "WEEK": MICRO_SECONDS * 3600 * 24 * 7,
                       "MONTH": MICRO_SECONDS * 3600 * 24 * 30
                      }

    CLIENT_CONFIG_KEY_PATTERN = {"GLOBAL": "{client_id}:S:GLOBAL",
                                 "METHOD": "{client_id}:S:METHOD:{http_method}",
                                 "API": "{client_id}:S:API:{api_url}"
                                 }

    REQUEST_LOGGED_KEY_PATTERN = {"GLOBAL": "{client_id}:C:GLOBAL",
                                  "METHOD": "{client_id}:C:METHOD:{http_method}",
                                  "API": "{client_id}:C:API:{api_url}"
                                  }

    def __init__(self):
        conn_pool = redis.ConnectionPool(host=settings.REDIS_CRED["HOST"],
                                         port=settings.REDIS_CRED["PORT"],
                                         db=settings.REDIS_RATE_LIMIT_DB,
                                         encoding='utf-8', decode_responses=True)
        self.r_ins = redis.Redis(connection_pool=conn_pool)

    def check_policy_exists(self, client_id):
        # Assumption: If no rate limiting configuration exists, then client
        # is not allowed to make any request
        # Client config regex is of the form "<client_id>:S:".
        # The specialization config keys are of following pattern:
        # "<client_id>:S:GLOBAL" ,
        # "<client_id>:S:METHOD:<http_method>",
        # "<client_id>:S:API:<api_url>"
        client_config_regex = '{client_id}:S:*'.format(client_id=client_id)
        found_keys = self.r_ins.keys(client_config_regex)
        return bool(found_keys)

    def fetch_configured_rate_limit(self, client_id, http_method, url):
        data = {"client_id": client_id, "http_method": http_method, "api_url": url}
        # Start queries single transaction.
        # Redis MULTI command wrapped under pipeline in redis-py
        pipe = self.r_ins.pipeline()
        # Global configuration
        pipe.hgetall(self.CLIENT_CONFIG_KEY_PATTERN['GLOBAL'].format(**data))
        # Specialization at HTTP method level
        pipe.hgetall(self.CLIENT_CONFIG_KEY_PATTERN['METHOD'].format(**data))
        # Specialization at API level
        pipe.hgetall(self.CLIENT_CONFIG_KEY_PATTERN['API'].format(**data))
        client_config = pipe.execute()
        #
        global_limit, method_spec_limit, api_spec_limit = client_config[0], client_config[1], client_config[2]
        return global_limit, method_spec_limit, api_spec_limit

    def check_rate_limit_violation(self, client_id, http_method, url, current_ts):
        # Fetch rate limit config
        global_limit, method_spec_limit, api_spec_limit = self.fetch_configured_rate_limit(client_id, http_method, url)

        # Get current running total
        data = {"client_id": client_id, "http_method": http_method, "api_url": url}
        # Possible specialization levels for a request.
        global_level_key = self.REQUEST_LOGGED_KEY_PATTERN['GLOBAL'].format(**data)
        method_level_key = self.REQUEST_LOGGED_KEY_PATTERN['METHOD'].format(**data)
        endpoint_level_key = self.REQUEST_LOGGED_KEY_PATTERN['API'].format(**data)

        # Fetch all data in single request using MULTI/EXEC.
        pipe = self.r_ins.pipeline()
        # Get the used capacity for each of the windows in MEASURE_UNIT.
        # We are using Sliding window algorithm for limiting requests
        for key in [global_level_key, method_level_key, endpoint_level_key]:
            for measure in self.MEASURE_UNIT:
                pipe.zcount(key, (current_ts - self.MICRO_SEC_COUNT[measure]), current_ts)
        curr_counts = pipe.execute()

        """
        Each of For loop sections below compare the current window with standard configuration
        As soon as a violation found, it returns.
        """
        limit_crossed = False

        # Check if global rate limit has crossed
        for index, measure in enumerate(self.MEASURE_UNIT, 0):
            if not limit_crossed:
                limit_crossed = (global_limit.get(measure) is not None and curr_counts[index] > int(global_limit[measure]))
        if limit_crossed:
            return True

        # Check if METHOD level rate limit has crossed
        for index, measure in enumerate(self.MEASURE_UNIT, 5):
            if not limit_crossed:
                limit_crossed = (method_spec_limit.get(measure) is not None and curr_counts[index] > int(method_spec_limit[measure]))
        if limit_crossed:
            return True

        # Check if API level rate limit has crossed
        for index, measure in enumerate(self.MEASURE_UNIT, 10):
            if not limit_crossed:
                limit_crossed = (api_spec_limit.get(measure) is not None and curr_counts[index] > int(api_spec_limit[measure]))
        if limit_crossed:
            return True

        """
        No violation found, so request would proceed and
        this request will +1 the count of respective rate-limiting-window
        """
        # add +1 to the count. MULTI/EXEC
        pipe = self.r_ins.pipeline()
        if global_limit:
            biggest_window = [_ for _ in self.MEASURE_UNIT if global_limit.get(_)][-1]
            pipe.zremrangebyscore(global_level_key, 0, (current_ts - self.MICRO_SEC_COUNT[biggest_window]))
            pipe.zadd(global_level_key, current_ts, current_ts)
            pipe.expire(global_level_key, self.MICRO_SEC_COUNT[biggest_window])
        if method_spec_limit:
            biggest_window = [_ for _ in self.MEASURE_UNIT if method_spec_limit.get(_)][-1]
            pipe.zremrangebyscore(method_level_key, 0, (current_ts - self.MICRO_SEC_COUNT[biggest_window]))
            pipe.zadd(method_level_key, current_ts, current_ts)
            pipe.expire(method_level_key, self.MICRO_SEC_COUNT[biggest_window])
        if api_spec_limit:
            biggest_window = [_ for _ in self.MEASURE_UNIT if api_spec_limit.get(_)][-1]
            pipe.zremrangebyscore(endpoint_level_key, 0, (current_ts - self.MICRO_SEC_COUNT[biggest_window]))
            pipe.zadd(endpoint_level_key, current_ts, current_ts)
            pipe.expire(endpoint_level_key, self.MICRO_SEC_COUNT[biggest_window])
        pipe.execute()

    def check_policy(self, client_id, http_method, url):
        # Current timestamp in micro-second,
        curr_timestamp = int(datetime.now().timestamp() * self.MICRO_SECONDS)
        limit_crossed = self.check_rate_limit_violation(client_id, http_method, url, curr_timestamp)
        return bool(limit_crossed)

    def load_policy_in_redis(self):
        from rate_limit.models import ClientRateLimitConfig
        import pdb; pdb.set_trace()
        configs = ClientRateLimitConfig.fetch_all_config()
        pipe = self.r_ins.pipeline()
        for client_id, client_conf in configs.items():
            for k, v in client_conf.items():
                pipe.hmset(k, v)
        pipe.execute()
