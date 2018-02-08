# Synopsis
 - Distributed-Rate-Limiting in Django App
 - A basic Django project setup to illustrate Distributed-Rate-Limiting using Django-middleware.
The core components include a middleware and a RateLimitPolicyChecker  
```
rate_limit.middleware.request_rate_limit.RequestRateLimitingMiddleware
rate_limit.middleware.rate_limit_policy.RateLimitPolicy
```

This middleware and policy can be used in any Distributed django app.  

## Getting started
1. Setup virtualenv for a django project. `virtualenv -p python3 <venv-name>`
2. Clone the git repo `git clone https://github.com/sk902/rate_limit.git`
3. Install required packages in the virtualenv, using `pip install -r requirements.txt`
4. Once setup is ready. Load sample Rate-limit configuration
	 ```
	 from rate_limit.script import create_sample_rate_limit_config_in_db, load_policy_in_redis
	 # Create Sample Rate-limit policy in DB (Postgres, in this instance)  
	 create_sample_rate_limit_config_in_db()
	 # Load the policy from DB to redis
	 load_policy_in_redis()	 
	 ```

### Configuration for a client
For a client, Rate Limiting policy can be at multiple levels viz. Global-limit, Limit-at-Specialization-levels  (e.g. HTTP-METHOD / API-ENDPOINT).
And for each level, there can be multiple time-windows among `SEC, MIN, HOUR, WEEK, MONTH` 

e.g
```
	client: <CLIENT-ID>
	limit:
		SEC -> int (Optional)
		MIN -> int (Optional)
		HOUR -> int (Optional)
		WEEK -> int (Optional)
		MONTH  -> int (Optional)
	specialization:
	    type: METHOD
			- <METHOD 1>: 
				limit:
					SEC -> int (Optional)
					MIN -> int (Optional)
					HOUR -> int (Optional)
					WEEK -> int (Optional)
					MONTH  -> int (Optional)
			- <METHOD 2> :
				limit:
					SEC -> int (Optional)
					MIN -> int (Optional)
					HOUR -> int (Optional)
					WEEK -> int (Optional)
					MONTH  -> int (Optional)
	    type: API
			- <API 1>:
				limit:
					SEC -> int (Optional)
					MIN -> int (Optional)
					HOUR -> int (Optional)
					WEEK -> int (Optional)
					MONTH  -> int (Optional)
			- <API 2>:
				limit:
					SEC -> int (Optional)
					MIN -> int (Optional)
					HOUR -> int (Optional)
					WEEK -> int (Optional)
					MONTH  -> int (Optional)
```

### Implementation Logic
It uses Redis for rate-limiting requests from client. 
All apps/services in the distributed cluster points to same redis DB. 

The Policy Checker uses `Sliding Window Algorithm` to check for rate-limit overflow 
at different levels and time-windows.  

Every request coming from client must have `HTTP_AUTHORIZATION=<client_id>` in http-header.
Response will be as follows:
1. API will return "UnAuthorizedRequest" if client_id is NULL or 
 if there is no rate-limit configured for given client_id.
 `{"code": 403 , "message": "Forbidden"}`
2. If request crosses the configured RateLimit, it will return TOO_MANY_REQUESTS.
 `{"code": 429, "message": "Rate limit exceeded"}`
3. If request passes the rate-limit check, the request will be passed forward for further processing.
