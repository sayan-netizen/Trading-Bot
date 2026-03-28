"""
Binance Futures Testnet REST client.

Handles:
- HMAC-SHA256 request signing
- Timestamping
- Structured request/response logging
- Retry on transient network errors
- Uniform exception mapping → BinanceClientError
"""

from __future__ import annotations

import hashlib
import hmac
import time
import urllib.parse
from decimal import Decimal
from typing import Any, Dict, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from bot.logging_config import setup_logger

class BinanceClientError(Exception):
    """Raised for any Binance API or network error."""

    def __init__(self, message: str, code: Optional[int] = None, raw: Any = None):
        super().__init__(message)
        self.code = code
        self.raw  = raw

    def __str__(self) -> str:
        if self.code:
            return f"[{self.code}] {super().__str__()}"
        return super().__str__()


class BinanceFuturesClient:
    """
    Thin wrapper around the Binance USDT-M Futures REST API.

    Args:
        api_key:    Binance API key.
        api_secret: Binance API secret.
        base_url:   Testnet or mainnet base URL.
        timeout:    HTTP request timeout in seconds.
        recv_window: Allowed timestamp drift in milliseconds.
    """

    DEFAULT_BASE_URL = "https://testnet.binancefuture.com"

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: int = 10,
        recv_window: int = 5000,
    ) -> None:
        if not api_key or not api_secret:
            raise ValueError("API key and secret must not be empty.")

        self._api_key    = api_key
        self._api_secret = api_secret.encode()
        self.base_url    = base_url.rstrip("/")
        self.timeout     = timeout
        self.recv_window = recv_window

        self._logger = setup_logger("binance_client")

        retry = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "DELETE"],
        )
        adapter = HTTPAdapter(max_retries=retry)
        self._session = requests.Session()
        self._session.mount("https://", adapter)
        self._session.headers.update({
            "X-MBX-APIKEY": self._api_key,
            "Content-Type": "application/x-www-form-urlencoded",
        })

    def _timestamp(self) -> int:
        return int(time.time() * 1000)

    def _sign(self, params: Dict[str, Any]) -> str:
        """Return HMAC-SHA256 hex signature for the given param dict."""
        query_string = urllib.parse.urlencode(params)
        return hmac.new(
            self._api_secret, query_string.encode(), hashlib.sha256
        ).hexdigest()

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        signed: bool = False,
    ) -> Dict[str, Any]:
        """
        Execute an HTTP request.

        Args:
            method:   "GET" | "POST" | "DELETE"
            endpoint: Path starting with "/" (e.g. "/fapi/v1/order")
            params:   Query / body parameters.
            signed:   Whether to add timestamp + signature.

        Returns:
            Parsed JSON response dict.

        Raises:
            BinanceClientError: on network failure or API error.
        """
        url = self.base_url + endpoint
        params = params or {}

        if signed:
            params["timestamp"]  = self._timestamp()
            params["recvWindow"] = self.recv_window
            params["signature"]  = self._sign(params)

        self._logger.debug(
            "→ %s %s | params: %s",
            method,
            endpoint,
            {k: v for k, v in params.items() if k != "signature"},
        )

        try:
            if method == "GET":
                response = self._session.get(url, params=params, timeout=self.timeout)
            elif method == "POST":
                response = self._session.post(url, data=params, timeout=self.timeout)
            elif method == "DELETE":
                response = self._session.delete(url, params=params, timeout=self.timeout)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
        except requests.ConnectionError as exc:
            self._logger.error("Network connection error: %s", exc)
            raise BinanceClientError(f"Network connection error: {exc}") from exc
        except requests.Timeout as exc:
            self._logger.error("Request timed out: %s", exc)
            raise BinanceClientError(f"Request timed out after {self.timeout}s.") from exc
        except requests.RequestException as exc:
            self._logger.error("Unexpected request error: %s", exc)
            raise BinanceClientError(f"Request failed: {exc}") from exc

        self._logger.debug(
            "← %s %s | status: %s | body: %.500s",
            method,
            endpoint,
            response.status_code,
            response.text,
        )

        try:
            data = response.json()
        except ValueError:
            raise BinanceClientError(
                f"Non-JSON response (HTTP {response.status_code}): {response.text[:200]}"
            )

        if not response.ok or (isinstance(data, dict) and "code" in data and data["code"] < 0):
            code = data.get("code") if isinstance(data, dict) else response.status_code
            msg  = data.get("msg", response.reason) if isinstance(data, dict) else response.text
            self._logger.error("API error [%s]: %s", code, msg)
            raise BinanceClientError(msg, code=code, raw=data)

        return data

    def ping(self) -> bool:
        """Return True if the API is reachable."""
        try:
            self._request("GET", "/fapi/v1/ping")
            return True
        except BinanceClientError:
            return False

    def get_server_time(self) -> int:
        """Return Binance server time in milliseconds."""
        data = self._request("GET", "/fapi/v1/time")
        return data["serverTime"]

    def get_account_info(self) -> Dict[str, Any]:
        """Return USDT-M futures account information."""
        return self._request("GET", "/fapi/v2/account", signed=True)

    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: Decimal,
        price: Optional[Decimal] = None,
        stop_price: Optional[Decimal] = None,
        time_in_force: str = "GTC",
    ) -> Dict[str, Any]:
        """
        Place a futures order.

        Args:
            symbol:        Trading pair (e.g. "BTCUSDT").
            side:          "BUY" or "SELL".
            order_type:    "MARKET", "LIMIT", or "STOP_MARKET".
            quantity:      Order quantity.
            price:         Limit price (LIMIT orders only).
            stop_price:    Trigger price (STOP_MARKET orders only).
            time_in_force: "GTC" | "IOC" | "FOK" (ignored for MARKET).

        Returns:
            Raw order response dict from Binance.
        """
        params: Dict[str, Any] = {
            "symbol":   symbol,
            "side":     side,
            "type":     order_type,
            "quantity": str(quantity),
        }

        if order_type == "LIMIT":
            params["price"]       = str(price)
            params["timeInForce"] = time_in_force

        if order_type == "STOP_MARKET":
            params["type"]         = "STOP_MARKET"
            params["algoType"]     = "CONDITIONAL"
            params["triggerPrice"] = str(stop_price)
            params.pop("quantity", None)
            params["quantity"]     = str(quantity)

        self._logger.info(
            "Placing %s %s order | symbol=%s qty=%s price=%s stopPrice=%s",
            side,
            order_type,
            symbol,
            quantity,
            price,
            stop_price,
        )

        endpoint = "/fapi/v1/algoOrder" if order_type == "STOP_MARKET" else "/fapi/v1/order"
        result = self._request("POST", endpoint, params=params, signed=True)
        self._logger.info(
            "Order accepted | orderId=%s status=%s",
            result.get("orderId"),
            result.get("status"),
        )
        return result

    def cancel_order(self, symbol: str, order_id: int) -> Dict[str, Any]:
        """Cancel an open order by ID."""
        params = {"symbol": symbol, "orderId": order_id}
        return self._request("DELETE", "/fapi/v1/order", params=params, signed=True)

    def get_open_orders(self, symbol: Optional[str] = None) -> list:
        """Return a list of currently open orders."""
        params: Dict[str, Any] = {}
        if symbol:
            params["symbol"] = symbol
        return self._request("GET", "/fapi/v1/openOrders", params=params, signed=True)