from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class BrokerSession:
    access_token: str | None = None
    refresh_token: str | None = None
    feed_token: str | None = None
    profile: dict = field(default_factory=dict)


@dataclass
class BrokerSnapshot:
    profile: dict
    holdings: list[dict]
    orders: list[dict]
    trades: list[dict]
    positions: list[dict]
    rms: dict


class BrokerAdapter(ABC):
    @abstractmethod
    async def connect(self, client_code: str, pin: str, totp: str) -> BrokerSession:
        raise NotImplementedError

    @abstractmethod
    async def fetch_snapshot(self) -> BrokerSnapshot:
        raise NotImplementedError

