from limits import parse, strategies
from limits.storage import storage_from_string


class ArcLimiter:
    storage = storage_from_string("memory://")
    strategy = strategies.FixedWindowRateLimiter(storage)

    def __init__(self, limit: str = None, namespace: str = None):
        self._limit = None
        self.limit = limit
        self.namespace = namespace

    @property
    def limit(self):
        return self._limit

    @limit.setter
    def limit(self, value):
        if value is None:
            return
        self._limit = parse(value)

    def hit(self, key: str, cost: int = 1) -> bool:
        return self.strategy.hit(self.limit, self.namespace, key, cost=cost)

    def test(self, key: str) -> bool:
        return self.strategy.test(self.limit, self.namespace, key)
