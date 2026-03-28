"""
Order placement logic for the Binance Futures Trading Bot.

Coordinates validation → client call → response formatting.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, Optional

from bot.client import BinanceFuturesClient, BinanceClientError
from bot.validators import validate_order_inputs
from bot.logging_config import setup_logger

logger = setup_logger("orders")

class OrderResult:
    """Holds a normalised view of a Binance order response."""

    def __init__(self, raw: Dict[str, Any]) -> None:
        self.raw          = raw
        self.order_id     = raw.get("orderId")
        self.client_id    = raw.get("clientOrderId")
        self.symbol       = raw.get("symbol")
        self.side         = raw.get("side")
        self.order_type   = raw.get("type")
        self.status       = raw.get("status")
        self.orig_qty     = raw.get("origQty")
        self.executed_qty = raw.get("executedQty")
        self.avg_price    = raw.get("avgPrice")
        self.price        = raw.get("price")
        self.stop_price   = raw.get("stopPrice")
        self.time_in_force = raw.get("timeInForce")
        self.update_time  = raw.get("updateTime")

    def summary(self) -> str:
        """Return a human-readable multi-line summary."""
        lines = [
            "",
            "╔══════════════════════════════════════════════╗",
            "║           ORDER RESPONSE SUMMARY             ║",
            "╚══════════════════════════════════════════════╝",
            f"  Order ID      : {self.order_id}",
            f"  Client OID    : {self.client_id}",
            f"  Symbol        : {self.symbol}",
            f"  Side          : {self.side}",
            f"  Type          : {self.order_type}",
            f"  Status        : {self.status}",
            f"  Orig Qty      : {self.orig_qty}",
            f"  Executed Qty  : {self.executed_qty}",
        ]
        if self.avg_price and float(self.avg_price) > 0:
            lines.append(f"  Avg Fill Price : {self.avg_price}")
        if self.price and float(self.price) > 0:
            lines.append(f"  Limit Price   : {self.price}")
        if self.stop_price and float(self.stop_price) > 0:
            lines.append(f"  Stop Price    : {self.stop_price}")
        if self.time_in_force:
            lines.append(f"  Time-in-Force : {self.time_in_force}")
        lines.append("──────────────────────────────────────────────")
        status_line = (
            "  ✅  Order placed successfully!"
            if self.status in ("NEW", "FILLED", "PARTIALLY_FILLED")
            else f"  ⚠️   Unexpected status: {self.status}"
        )
        lines.append(status_line)
        lines.append("")
        return "\n".join(lines)

def place_order(
    client: BinanceFuturesClient,
    symbol: str,
    side: str,
    order_type: str,
    quantity: str | float,
    price: Optional[str | float] = None,
    stop_price: Optional[str | float] = None,
    time_in_force: str = "GTC",
) -> OrderResult:
    """
    Validate inputs, place the order, and return an OrderResult.

    Args:
        client:        Authenticated BinanceFuturesClient.
        symbol:        e.g. "BTCUSDT"
        side:          "BUY" | "SELL"
        order_type:    "MARKET" | "LIMIT" | "STOP_MARKET"
        quantity:      Order quantity (string or float).
        price:         Required for LIMIT.
        stop_price:    Required for STOP_MARKET.
        time_in_force: Default "GTC".

    Returns:
        OrderResult wrapping the raw Binance response.

    Raises:
        ValueError:          on validation failure.
        BinanceClientError:  on API or network failure.
    """
    logger.debug(
        "validate_order_inputs | symbol=%s side=%s type=%s qty=%s price=%s stop=%s",
        symbol, side, order_type, quantity, price, stop_price,
    )
    validated = validate_order_inputs(
        symbol=symbol,
        side=side,
        order_type=order_type,
        quantity=quantity,
        price=price,
        stop_price=stop_price,
    )

    _print_request_summary(validated)

    raw = client.place_order(
        symbol       = validated["symbol"],
        side         = validated["side"],
        order_type   = validated["order_type"],
        quantity     = validated["quantity"],
        price        = validated["price"],
        stop_price   = validated["stop_price"],
        time_in_force= time_in_force,
    )

    result = OrderResult(raw)
    logger.info(
        "Order result | orderId=%s status=%s executedQty=%s avgPrice=%s",
        result.order_id,
        result.status,
        result.executed_qty,
        result.avg_price,
    )
    return result

def _print_request_summary(validated: Dict[str, Any]) -> None:
    """Print a formatted order request summary to stdout."""
    price_str = str(validated["price"]) if validated["price"] else "N/A (MARKET)"
    stop_str  = str(validated["stop_price"]) if validated["stop_price"] else "—"
    print(
        "\n"
        "┌──────────────────────────────────────────────┐\n"
        "│             ORDER REQUEST SUMMARY            │\n"
        "├──────────────────────────────────────────────┤\n"
        f"│  Symbol     : {validated['symbol']:<31}│\n"
        f"│  Side       : {validated['side']:<31}│\n"
        f"│  Type       : {validated['order_type']:<31}│\n"
        f"│  Quantity   : {str(validated['quantity']):<31}│\n"
        f"│  Price      : {price_str:<31}│\n"
        f"│  Stop Price : {stop_str:<31}│\n"
        "└──────────────────────────────────────────────┘"
    )
