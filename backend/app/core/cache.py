"""Cache TTL en memoria para queries costosas y de baja variabilidad.

Reduce la carga en Postgres cuando estos endpoints reciben tráfico de
volumen (sea legítimo o abusivo): los datos subyacentes (dataset público +
resultados reales) solo cambian cuando entra un diagnóstico nuevo, así que
recalcular en cada request es trabajo desperdiciado.

Es un cache por-proceso, no distribuido: en serverless cada instancia tiene
el suyo. No reemplaza un rate limit real, pero baja el costo por hit.
"""

import time
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import ParamSpec, TypeVar

P = ParamSpec("P")
T = TypeVar("T")


def ttl_cache(seconds: float) -> Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T]]]:
    def decorator(fn: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
        store: dict[tuple, tuple[float, T]] = {}

        @wraps(fn)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            key = (args, tuple(sorted(kwargs.items())))
            now = time.monotonic()
            cached = store.get(key)
            if cached is not None and now < cached[0]:
                return cached[1]

            value = await fn(*args, **kwargs)
            store[key] = (now + seconds, value)
            return value

        return wrapper

    return decorator
