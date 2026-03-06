from django.core.cache import cache
from commons.exceptions.rate_limiting import ResendMaxLimit


def rate_limit(limit, period, cache_key_prefix='rate_limit'):
    """
    Decorator to rate limit access to views using Redis.
    :param limit: Maximum number of requests allowed
    :param period: Time period in seconds for the rate limit
    :param cache_key_prefix: Redis cache key prefix
    """

    def decorator(func):
        def wrapper(_self, request, *args, **kwargs):
            user_id = request.user.id if request.user.is_authenticated else request.META.get('REMOTE_ADDR')
            cache_key = f'{cache_key_prefix}:{user_id}:{request.path}'

            # Get the current count of requests from Redis
            request_count = cache.get(cache_key, 0)

            # If the limit is reached, deny access
            if request_count >= limit:
                raise ResendMaxLimit()

            # Otherwise, increment the request count
            cache.set(cache_key, request_count + 1, timeout=period)

            # Call the actual view function
            return func(_self, request, *args, **kwargs)

        return wrapper

    return decorator
