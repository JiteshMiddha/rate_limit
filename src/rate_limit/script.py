__author__ = 'sanjeev'


def create_sample_rate_limit_config_in_db():
    data = [dict(client_id="CLIENT_1",
                 global_limit={
                     "SEC": 10, "MIN": 30, "HOUR": 200, "WEEK": 10000, "MONTH": 100000
                 },
                 method_limits=[
                     {
                         "http_method": "GET",
                         "limit": {"SEC": 10, "MIN": 30, "HOUR": 200, "WEEK": 10000, "MONTH": 100000}
                     }, {
                         "http_method": "POST",
                         "limit": {"SEC": 2, "MIN": 10, "HOUR": 100, "WEEK": 1000, "MONTH": 2000}
                     }
                 ],
                 end_point=[
                     {
                         "url": "/status/",
                         "limit": {"SEC": 2, "MIN": 10, "HOUR": 100, "WEEK": 1000, "MONTH": 2000}
                     },
                     {
                         "url": "/pay/",
                         "limit": {"SEC": 2, "MIN": 10, "HOUR": 100, "WEEK": 1000, "MONTH": 2000}
                     }
                 ]
                 ),
            ]
    from rate_limit.models import ClientRateLimitConfig
    ClientRateLimitConfig.create_rate_limit_entry(data)


def load_policy_in_redis():
    from rate_limit.middleware.rate_limit_policy import RateLimitPolicy
    policy = RateLimitPolicy()
    policy.load_policy_in_redis()
