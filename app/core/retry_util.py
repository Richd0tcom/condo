from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)
from functools import wraps
import logging
import httpx
from typing import Callable, Any, Optional, List, Type
import asyncio

logger = logging.getLogger(__name__)

class RetryableError(Exception):
    """Base class for retryable errors"""
    pass

class ExternalServiceError(RetryableError):
    """External service temporarily unavailable"""
    pass

class RateLimitError(RetryableError):
    """Rate limit exceeded"""
    pass

def create_retry_decorator(
    max_attempts: int = 3,
    wait_multiplier: float = 1,
    wait_max: float = 60,
    retry_exceptions: Optional[List[Type[Exception]]] = None
):
    """Create a customizable retry decorator"""
    if retry_exceptions is None:
        retry_exceptions = [RetryableError, httpx.HTTPError, ConnectionError]
    
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=wait_multiplier, max=wait_max),
        retry=retry_if_exception_type(tuple(retry_exceptions)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True
    )

external_api_retry = create_retry_decorator(
    max_attempts=3,
    wait_multiplier=2,
    wait_max=30,
    retry_exceptions=[
        httpx.HTTPError,
        httpx.ConnectError,
        httpx.TimeoutException,
        ExternalServiceError,
        RateLimitError
    ]
)

def async_retry(
    max_attempts: int = 3,
    wait_multiplier: float = 1,
    wait_max: float = 60,
    retry_exceptions: Optional[List[Type[Exception]]] = None
):
    """Async retry decorator"""
    if retry_exceptions is None:
        retry_exceptions = [RetryableError, httpx.HTTPError, ConnectionError]
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            attempt = 0
            while attempt < max_attempts:
                try:
                    return await func(*args, **kwargs)
                except tuple(retry_exceptions) as e:
                    attempt += 1
                    if attempt >= max_attempts:
                        logger.error(f"Max retries ({max_attempts}) exceeded for {func.__name__}: {e}")
                        raise
                    
                    wait_time = min(wait_multiplier * (2 ** (attempt - 1)), wait_max)
                    logger.warning(f"Attempt {attempt} failed for {func.__name__}: {e}. Retrying in {wait_time}s")
                    await asyncio.sleep(wait_time)
            
        return wrapper
    return decorator