import time
import asyncio
from enum import Enum
from typing import Callable, Any, Optional, Dict
from functools import wraps
import logging
from dataclasses import dataclass, field

import structlog

logger = structlog.get_logger(__name__)

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 5
    recovery_timeout: float = 60.0
    expected_exception: type = Exception
    name: str = "CircuitBreaker"

@dataclass
class CircuitBreakerStats:
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[float] = None
    state: CircuitState = CircuitState.CLOSED
    
class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open"""
    pass

class CircuitBreaker:
    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.stats = CircuitBreakerStats()
        self._lock = asyncio.Lock()
    
    async def __aenter__(self):
        await self._check_state()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            await self._on_success()
        elif issubclass(exc_type, self.config.expected_exception):
            await self._on_failure()
        return False
    
    async def _check_state(self):
        async with self._lock:
            if self.stats.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.stats.state = CircuitState.HALF_OPEN
                    logger.info(f"Circuit breaker {self.config.name} moving to HALF_OPEN")
                else:
                    raise CircuitBreakerError(f"Circuit breaker {self.config.name} is OPEN")
    
    def _should_attempt_reset(self) -> bool:
        return (
            self.stats.last_failure_time is not None and
            time.time() - self.stats.last_failure_time >= self.config.recovery_timeout
        )
    
    async def _on_success(self):
        async with self._lock:
            self.stats.success_count += 1
            if self.stats.state == CircuitState.HALF_OPEN:
                self.stats.state = CircuitState.CLOSED
                self.stats.failure_count = 0
                logger.info(f"Circuit breaker {self.config.name} reset to CLOSED")
    
    async def _on_failure(self):
        async with self._lock:
            self.stats.failure_count += 1
            self.stats.last_failure_time = time.time()
            
            if (self.stats.state == CircuitState.CLOSED and 
                self.stats.failure_count >= self.config.failure_threshold):
                self.stats.state = CircuitState.OPEN
                logger.warning(f"Circuit breaker {self.config.name} opened after {self.stats.failure_count} failures")
            elif self.stats.state == CircuitState.HALF_OPEN:
                self.stats.state = CircuitState.OPEN
                logger.warning(f"Circuit breaker {self.config.name} reopened on failure")

_circuit_breakers: Dict[str, CircuitBreaker] = {}

def get_circuit_breaker(name: str, config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
    """Get or create a circuit breaker instance"""
    if name not in _circuit_breakers:
        if config is None:
            config = CircuitBreakerConfig(name=name)
        _circuit_breakers[name] = CircuitBreaker(config)
    return _circuit_breakers[name]

def circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    recovery_timeout: float = 60.0,
    expected_exception: type = Exception
):
    """Circuit breaker decorator"""
    config = CircuitBreakerConfig(
        failure_threshold=failure_threshold,
        recovery_timeout=recovery_timeout,
        expected_exception=expected_exception,
        name=name
    )
    
    def decorator(func: Callable) -> Callable:
        breaker = get_circuit_breaker(name, config)
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            async with breaker:
                return await func(*args, **kwargs)
        
        return wrapper
    return decorator