"""
Input validation for the Binance Futures Trading Bot.
All validation functions raise ValueError with descriptive messages on failure.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Optional


VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT", "STOP_MARKET"}

def validate_symbol(symbol: str) -> str:
    """Return uppercased symbol if non-empty, else raise ValueError."""
    symbol = symbol.strip().upper()
    if not symbol:
        raise ValueError("Symbol must not be empty (e.g. BTCUSDT).")
    if not symbol.isalnum():
        raise ValueError(f"Symbol '{symbol}' contains invalid characters.")
    return symbol


def validate_side(side: str) -> str:
    """Return uppercased side if valid, else raise ValueError."""
    side = side.strip().upper()
    if side not in VALID_SIDES:
        raise ValueError(
            f"Side '{side}' is invalid. Choose from: {', '.join(sorted(VALID_SIDES))}."
        )
    return side


def validate_order_type(order_type: str) -> str:
    """Return uppercased order type if valid, else raise ValueError."""
    order_type = order_type.strip().upper()
    if order_type not in VALID_ORDER_TYPES:
        raise ValueError(
            f"Order type '{order_type}' is invalid. "
            f"Choose from: {', '.join(sorted(VALID_ORDER_TYPES))}."
        )
    return order_type


def validate_quantity(quantity: str | float) -> Decimal:
    """Parse and validate quantity; must be a positive decimal."""
    try:
        qty = Decimal(str(quantity))
    except InvalidOperation:
        raise ValueError(f"Quantity '{quantity}' is not a valid number.")
    if qty <= 0:
        raise ValueError(f"Quantity must be greater than 0. Got: {qty}.")
    return qty


def validate_price(price: Optional[str | float], order_type: str) -> Optional[Decimal]:
    """
    Parse and validate price.
    - Required (and must be positive) when order_type is LIMIT.
    - Must be None / omitted for MARKET and STOP_MARKET orders.
    """
    order_type = order_type.upper()

    if order_type in ("MARKET", "STOP_MARKET"):
        if price is not None:
            raise ValueError("Price must not be provided for MARKET or STOP_MARKET orders.")
        return None

    if price is None or str(price).strip() == "":
        raise ValueError(f"Price is required for {order_type} orders.")
    try:
        p = Decimal(str(price))
    except InvalidOperation:
        raise ValueError(f"Price '{price}' is not a valid number.")
    if p <= 0:
        raise ValueError(f"Price must be greater than 0. Got: {p}.")
    return p


def validate_stop_price(
    stop_price: Optional[str | float], order_type: str
) -> Optional[Decimal]:
    """Stop price is required only for STOP_MARKET orders."""
    order_type = order_type.upper()

    if order_type != "STOP_MARKET":
        return None

    if stop_price is None or str(stop_price).strip() == "":
        raise ValueError("Stop price (--stop-price) is required for STOP_MARKET orders.")
    try:
        sp = Decimal(str(stop_price))
    except InvalidOperation:
        raise ValueError(f"Stop price '{stop_price}' is not a valid number.")
    if sp <= 0:
        raise ValueError(f"Stop price must be greater than 0. Got: {sp}.")
    return sp

def validate_order_inputs(
    symbol: str,
    side: str,
    order_type: str,
    quantity: str | float,
    price: Optional[str | float] = None,
    stop_price: Optional[str | float] = None,
) -> dict:
    """
    Run all validations and return a clean params dict ready for order placement.

    Returns:
        {
            "symbol": str,
            "side": str,
            "order_type": str,
            "quantity": Decimal,
            "price": Decimal | None,
            "stop_price": Decimal | None,
        }

    Raises:
        ValueError: on any validation failure.
    """
    v_symbol     = validate_symbol(symbol)
    v_side       = validate_side(side)
    v_type       = validate_order_type(order_type)
    v_qty        = validate_quantity(quantity)
    v_price      = validate_price(price, v_type)
    v_stop_price = validate_stop_price(stop_price, v_type)

    return {
        "symbol":     v_symbol,
        "side":       v_side,
        "order_type": v_type,
        "quantity":   v_qty,
        "price":      v_price,
        "stop_price": v_stop_price,
    }