import socket
import uuid

import httpx

from app.broker.base import BrokerAdapter, BrokerSession, BrokerSnapshot


class AngelOneError(RuntimeError):
    pass


class AngelOneAdapter(BrokerAdapter):
    root_url = "https://apiconnect.angelone.in"

    def __init__(
        self,
        api_key: str,
        access_token: str | None = None,
        refresh_token: str | None = None,
        public_ip: str | None = None,
        local_ip: str | None = None,
        mac_address: str | None = None,
    ):
        self.api_key = api_key
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.public_ip = public_ip
        self.local_ip = local_ip
        self.mac_address = mac_address

    def _headers(self) -> dict[str, str]:
        hostname = socket.gethostname()
        try:
            local_ip = socket.gethostbyname(hostname)
        except socket.gaierror:
            local_ip = "127.0.0.1"
        mac = self.mac_address or ":".join(f"{(uuid.getnode() >> offset) & 0xff:02x}" for offset in range(40, -1, -8))
        client_local_ip = self.local_ip or local_ip
        client_public_ip = self.public_ip or local_ip
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-UserType": "USER",
            "X-SourceID": "WEB",
            "X-ClientLocalIP": client_local_ip,
            "X-ClientPublicIP": client_public_ip,
            "X-MACAddress": mac,
            "X-PrivateKey": self.api_key,
        }
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        return headers

    async def _request(self, method: str, path: str, payload: dict | None = None):
        async with httpx.AsyncClient(timeout=25) as client:
            response = await client.request(method, f"{self.root_url}{path}", headers=self._headers(), json=payload)
        try:
            body = response.json()
        except ValueError as exc:
            raise AngelOneError("Angel One returned an unreadable response") from exc
        if response.is_error or body.get("status") is False:
            raise AngelOneError(body.get("message") or "Angel One request failed")
        return body.get("data") or {}

    async def connect(self, client_code: str, pin: str, totp: str) -> BrokerSession:
        data = await self._request(
            "POST",
            "/rest/auth/angelbroking/user/v1/loginByPassword",
            {"clientcode": client_code, "password": pin, "totp": totp},
        )
        self.access_token = data.get("jwtToken")
        self.refresh_token = data.get("refreshToken")
        profile = await self._request(
            "POST",
            "/rest/secure/angelbroking/user/v1/getProfile",
            {"refreshToken": self.refresh_token},
        )
        return BrokerSession(
            access_token=self.access_token,
            refresh_token=self.refresh_token,
            feed_token=data.get("feedToken"),
            profile=profile,
        )

    async def fetch_snapshot(self) -> BrokerSnapshot:
        if not self.access_token:
            raise AngelOneError("Angel One session is missing. Reconnect the account.")
        profile = await self._request(
            "POST",
            "/rest/secure/angelbroking/user/v1/getProfile",
            {"refreshToken": self.refresh_token},
        )
        holdings = await self._request("GET", "/rest/secure/angelbroking/portfolio/v1/getAllHolding")
        orders = await self._request("GET", "/rest/secure/angelbroking/order/v1/getOrderBook")
        trades = await self._request("GET", "/rest/secure/angelbroking/order/v1/getTradeBook")
        positions = await self._request("GET", "/rest/secure/angelbroking/order/v1/getPosition")
        rms = await self._request("GET", "/rest/secure/angelbroking/user/v1/getRMS")
        holding_rows = holdings.get("holdings", holdings) if isinstance(holdings, dict) else holdings
        return BrokerSnapshot(
            profile=profile if isinstance(profile, dict) else {},
            holdings=holding_rows if isinstance(holding_rows, list) else [],
            orders=orders if isinstance(orders, list) else [],
            trades=trades if isinstance(trades, list) else [],
            positions=positions if isinstance(positions, list) else [],
            rms=rms if isinstance(rms, dict) else {},
        )
