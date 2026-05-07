from django.core.cache import cache
from functools import wraps
from hashlib import md5


def cached_function(timeout=300):
    """It caches the result of the provided function and improves performance."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = md5(
                f"{func.__module__}:{func.__name__}:{args}:{kwargs}".encode()
            ).hexdigest()

            _object = object()
            result = cache.get(cache_key, default=_object)
            if result is not _object:
                return result

            result = func(*args, **kwargs)
            cache.set(cache_key, result, timeout=timeout)
            return result

        return wrapper

    return decorator
