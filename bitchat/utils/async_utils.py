"""
Async utilities for Blue Relay Chat RPi 4 client.

This module provides utilities for working with async/await patterns
and concurrent operations.
"""

import asyncio
import time
from typing import Any, Awaitable, Callable, List, Optional, Union, Coroutine
from functools import wraps
from concurrent.futures import ThreadPoolExecutor

from ..exceptions import ValidationError


async def create_task(coro: Awaitable, name: Optional[str] = None) -> asyncio.Task:
    """
    Create an asyncio task with proper error handling.
    
    Args:
        coro: Coroutine to run as a task
        name: Optional name for the task
        
    Returns:
        Created task
    """
    task = asyncio.create_task(coro, name=name)
    
    # Add error handling to prevent task exceptions being lost
    def handle_exception(task: asyncio.Task):
        if not task.cancelled() and task.exception():
            try:
                import logging
                logger = logging.getLogger("async_utils")
                logger.error(f"Task {task.get_name() or 'unnamed'} failed: {task.exception()}")
            except Exception:
                # Avoid errors in error handling
                pass
    
    task.add_done_callback(handle_exception)
    return task


async def gather_with_concurrency(
    coros: List[Awaitable], 
    concurrency: int = 10,
    return_exceptions: bool = False
) -> List[Any]:
    """
    Gather coroutines with a concurrency limit.
    
    Args:
        coros: List of coroutines to run
        concurrency: Maximum number of concurrent tasks
        return_exceptions: Whether to return exceptions instead of raising
        
    Returns:
        List of results
    """
    if concurrency <= 0:
        raise ValidationError("Concurrency must be greater than 0")
    
    semaphore = asyncio.Semaphore(concurrency)
    
    async def limited_coro(coro: Awaitable) -> Any:
        async with semaphore:
            return await coro
    
    limited_coros = [limited_coro(coro) for coro in coros]
    return await asyncio.gather(*limited_coros, return_exceptions=return_exceptions)


async def wait_with_timeout(
    coro: Awaitable, 
    timeout: float, 
    default: Any = None
) -> Any:
    """
    Wait for a coroutine with a timeout and default value.
    
    Args:
        coro: Coroutine to wait for
        timeout: Timeout in seconds
        default: Default value if timeout occurs
        
    Returns:
        Coroutine result or default value
    """
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        return default


def run_in_thread(func: Callable, *args, **kwargs) -> Awaitable:
    """
    Run a function in a thread pool.
    
    Args:
        func: Function to run
        args: Function arguments
        kwargs: Function keyword arguments
        
    Returns:
        Awaitable that will return the function result
    """
    loop = asyncio.get_event_loop()
    
    with ThreadPoolExecutor() as executor:
        return loop.run_in_executor(executor, func, *args, **kwargs)


def async_cache(ttl: Optional[float] = None):
    """
    Decorator for caching async function results.
    
    Args:
        ttl: Time to live in seconds (None for no expiration)
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable):
        cache = {}
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Create cache key
            key = str(args) + str(sorted(kwargs.items()))
            
            # Check cache
            if key in cache:
                cached_item = cache[key]
                if ttl is None or time.time() - cached_item["time"] < ttl:
                    return cached_item["value"]
            
            # Call function and cache result
            result = await func(*args, **kwargs)
            cache[key] = {
                "value": result,
                "time": time.time()
            }
            
            return result
        
        wrapper.cache_clear = lambda: cache.clear()
        return wrapper
    
    return decorator


def debounce(delay: float):
    """
    Decorator for debouncing async function calls.
    
    Args:
        delay: Delay in seconds
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable):
        last_called = [0]
        task = [None]
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            now = time.time()
            
            # Cancel previous task if still running
            if task[0] and not task[0].done():
                task[0].cancel()
            
            # Schedule new call
            async def debounced_call():
                await asyncio.sleep(delay)
                last_called[0] = time.time()
                return await func(*args, **kwargs)
            
            task[0] = asyncio.create_task(debounced_call())
            return await task[0]
        
        return wrapper
    
    return decorator


def throttle(rate_limit: float):
    """
    Decorator for throttling async function calls.
    
    Args:
        rate_limit: Maximum calls per second
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable):
        min_interval = 1.0 / rate_limit
        last_called = [0]
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            now = time.time()
            elapsed = now - last_called[0]
            
            if elapsed < min_interval:
                await asyncio.sleep(min_interval - elapsed)
            
            last_called[0] = time.time()
            return await func(*args, **kwargs)
        
        return wrapper
    
    return decorator


def retry(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0, exceptions: tuple = (Exception,)):
    """
    Decorator for retrying async functions.
    
    Args:
        max_attempts: Maximum number of attempts
        delay: Initial delay between attempts
        backoff: Multiplier for delay after each attempt
        exceptions: Tuple of exceptions to catch
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt < max_attempts:
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
            
            # All attempts failed, raise the last exception
            raise last_exception
        
        return wrapper
    
    return decorator


class AsyncQueue:
    """Async queue with priority support."""
    
    def __init__(self, maxsize: int = 0):
        """
        Initialize the async queue.
        
        Args:
            maxsize: Maximum queue size (0 for unlimited)
        """
        self._queue = asyncio.PriorityQueue(maxsize=maxsize)
    
    async def put(self, item: Any, priority: int = 0) -> None:
        """
        Put an item in the queue.
        
        Args:
            item: Item to put
            priority: Priority (lower numbers = higher priority)
        """
        await self._queue.put((priority, item))
    
    async def get(self) -> Any:
        """
        Get an item from the queue.
        
        Returns:
            Queue item
        """
        priority, item = await self._queue.get()
        return item
    
    def empty(self) -> bool:
        """Check if the queue is empty."""
        return self._queue.empty()
    
    def full(self) -> bool:
        """Check if the queue is full."""
        return self._queue.full()
    
    def qsize(self) -> int:
        """Get the queue size."""
        return self._queue.qsize()
    
    async def join(self) -> None:
        """Wait until all items in the queue have been processed."""
        await self._queue.join()


class AsyncEvent:
    """Async event that can be waited on by multiple coroutines."""
    
    def __init__(self):
        """Initialize the async event."""
        self._event = asyncio.Event()
        self._value = None
    
    def set(self, value: Any = None) -> None:
        """
        Set the event.
        
        Args:
            value: Optional value to store with the event
        """
        self._value = value
        self._event.set()
    
    def is_set(self) -> bool:
        """Check if the event is set."""
        return self._event.is_set()
    
    def clear(self) -> None:
        """Clear the event."""
        self._event.clear()
        self._value = None
    
    async def wait(self) -> Any:
        """
        Wait for the event to be set.
        
        Returns:
            Event value
        """
        await self._event.wait()
        return self._value


class AsyncRateLimiter:
    """Async rate limiter."""
    
    def __init__(self, rate_limit: float, burst_size: int = 1):
        """
        Initialize the rate limiter.
        
        Args:
            rate_limit: Maximum calls per second
            burst_size: Maximum burst size
        """
        self.rate_limit = rate_limit
        self.burst_size = burst_size
        self.tokens = burst_size
        self.last_update = time.time()
        self._lock = asyncio.Lock()
    
    async def acquire(self) -> None:
        """Acquire a token from the rate limiter."""
        async with self._lock:
            now = time.time()
            
            # Update tokens based on time elapsed
            elapsed = now - self.last_update
            self.tokens = min(self.burst_size, self.tokens + elapsed * self.rate_limit)
            self.last_update = now
            
            # Check if we have a token
            if self.tokens < 1:
                # Calculate wait time
                wait_time = (1 - self.tokens) / self.rate_limit
                await asyncio.sleep(wait_time)
                self.tokens = 0
            else:
                self.tokens -= 1
    
    async def __aenter__(self):
        """Enter context manager."""
        await self.acquire()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager."""
        pass