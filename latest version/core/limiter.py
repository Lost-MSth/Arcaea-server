from limits import parse_many, strategies
from limits.storage import storage_from_string


class ArcLimiter:
    storage = storage_from_string("memory://")
    strategy = strategies.FixedWindowRateLimiter(storage)

    def __init__(self, limit_str: str = None, namespace: str = None):
        self._limits: list = None
        self.limits = limit_str
        self.namespace = namespace

    @property
    def limits(self) -> list:
        return self._limits

    @limits.setter
    def limits(self, value: str):
        if value is None:
            return
        self._limits = parse_many(value)

    def hit(self, key: str, cost: int = 1) -> bool:
        flag = True
        for limit in self.limits:
            flag &= self.strategy.hit(limit, self.namespace, key, cost)
        return flag

    def test(self, key: str) -> bool:
        return all(self.strategy.test(limit, self.namespace, key) for limit in self.limits)
