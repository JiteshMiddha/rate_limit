# dist_rate_limit
This is a Django project setup that includes a middleware for Distributed Rate Limiting.
The core logic of Rate-limiting is written in 
`rate_limit.middleware.request_rate_limit.RequestRateLimitingMiddleware` and  
`rate_limit.middleware.rate_limit_policy.RateLimitPolicy`

This middleware and policy can be used by any Distributed django app.  

# Setup
1. Clone the git repo `git clone https://github.com/sk902/rate_limit.git`
2. Setup virtualenv for django project. `virtualenv -p <python-3-path> <venv-name>`
3. Install required packages in the virtualenv, using `pip install -r requirements.txt`


# How It works
It uses Redis for managing the rate-limit. This redis db is pointed by all apps in the 
distributed setting. 

The PolicyChecker uses `Sliding Window Algorithm` to check for rate-limit crossing for any defined time-window. The time-window can be one or more among `SEC, MIN, HOUR, WEEK, MONTH` 
For a client, there can be policy at multiple levels viz. Global-limit, Limit-at-Specialization-levels 
(e.g. HTTP-METHOD / API-ENDPOINT):

Rate-limit Config for individual client
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
The configuration for each client is loaded in the redis with appropriate key.

Every request must have `HTTP_AUTHORIZATION=<client_id>` in http-header.

If client_id is NULL or if there is no rate-limit configured for given client_id, 
then response for Unauthorized request `{"code": 403 , "message": "Forbidden"}` will be sent. 
If request crosses the configured RateLimit, 
response for TOO_MANY_REQUESTS `{"code": 429, "message": "Rate limit exceeded"}` will be sent

If request passes the rate-limit check, the request will be passed forward
 for further processing. 
