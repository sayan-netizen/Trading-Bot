"""
Binance Futures Testnet Trading Bot — CLI entry point.

Usage examples:
    python cli.py place --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
    python cli.py place --symbol ETHUSDT --side SELL --type LIMIT --quantity 0.01 --price 3000
    python cli.py place --symbol BTCUSDT --side SELL --type STOP_MARKET --quantity 0.001 --stop-price 55000
    python cli.py orders --symbol BTCUSDT
    python cli.py ping
"""

from __future__ import annotations

import argparse
import json
import os
import sys

from dotenv import load_dotenv

from bot.client import BinanceFuturesClient, BinanceClientError
from bot.logging_config import setup_logger
from bot.orders import place_order

load_dotenv()
logger = setup_logger("cli")


def _get_client() -> BinanceFuturesClient:
    """Build a client from environment variables."""
    api_key    = os.getenv("BINANCE_API_KEY", "").strip()
    api_secret = os.getenv("BINANCE_API_SECRET", "").strip()
    base_url   = os.getenv("BINANCE_BASE_URL", BinanceFuturesClient.DEFAULT_BASE_URL)

    if not api_key or not api_secret:
        print(
            "\n❌  API credentials not found.\n"
            "    Set BINANCE_API_KEY and BINANCE_API_SECRET in your .env file or environment.\n",
            file=sys.stderr,
        )
        logger.error("Missing API credentials.")
        sys.exit(1)

    return BinanceFuturesClient(api_key=api_key, api_secret=api_secret, base_url=base_url)


def cmd_ping(args: argparse.Namespace) -> None:
    client = _get_client()
    if client.ping():
        print("\n✅  Binance Futures Testnet is reachable.\n")
        logger.info("Ping successful.")
    else:
        print("\n❌  Could not reach Binance Futures Testnet.\n", file=sys.stderr)
        logger.error("Ping failed.")
        sys.exit(1)


def cmd_place(args: argparse.Namespace) -> None:
    """Handle the 'place' sub-command."""
    client = _get_client()

    logger.info(
        "CLI place | symbol=%s side=%s type=%s qty=%s price=%s stop=%s",
        args.symbol, args.side, args.type, args.quantity, args.price, args.stop_price,
    )

    try:
        result = place_order(
            client       = client,
            symbol       = args.symbol,
            side         = args.side,
            order_type   = args.type,
            quantity     = args.quantity,
            price        = args.price,
            stop_price   = args.stop_price,
            time_in_force= args.tif,
        )
        print(result.summary())

    except ValueError as exc:
        print(f"\n❌  Validation error: {exc}\n", file=sys.stderr)
        logger.error("Validation error: %s", exc)
        sys.exit(2)

    except BinanceClientError as exc:
        print(f"\n❌  API error: {exc}\n", file=sys.stderr)
        logger.error("API error: %s", exc)
        sys.exit(3)


def cmd_orders(args: argparse.Namespace) -> None:
    """List open orders."""
    client = _get_client()
    try:
        orders = client.get_open_orders(symbol=args.symbol or None)
        if not orders:
            print("\n  No open orders found.\n")
            return
        print(f"\n  Open orders ({len(orders)}):\n")
        for o in orders:
            print(f"  • [{o['orderId']}] {o['symbol']} {o['side']} {o['type']} "
                  f"qty={o['origQty']} price={o.get('price','—')} status={o['status']}")
        print()
    except BinanceClientError as exc:
        print(f"\n❌  API error: {exc}\n", file=sys.stderr)
        logger.error("Failed to fetch open orders: %s", exc)
        sys.exit(3)


def cmd_account(args: argparse.Namespace) -> None:
    """Print a brief account summary."""
    client = _get_client()
    try:
        info = client.get_account_info()
        print(f"\n  Total Wallet Balance  : {info.get('totalWalletBalance')} USDT")
        print(f"  Total Unrealised PnL  : {info.get('totalUnrealizedProfit')} USDT")
        print(f"  Available Balance     : {info.get('availableBalance')} USDT")
        print()
    except BinanceClientError as exc:
        print(f"\n❌  API error: {exc}\n", file=sys.stderr)
        logger.error("Failed to fetch account info: %s", exc)
        sys.exit(3)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="trading_bot",
        description="Binance Futures Testnet Trading Bot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py ping
  python cli.py place --symbol BTCUSDT --side BUY  --type MARKET      --quantity 0.001
  python cli.py place --symbol ETHUSDT --side SELL --type LIMIT        --quantity 0.01  --price 3000
  python cli.py place --symbol BTCUSDT --side SELL --type STOP_MARKET  --quantity 0.001 --stop-price 55000
  python cli.py orders --symbol BTCUSDT
  python cli.py account
        """,
    )

    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("ping", help="Check connectivity to Binance Futures Testnet")

    place_p = sub.add_parser("place", help="Place a futures order")
    place_p.add_argument("--symbol",     required=True,  help="Trading pair  (e.g. BTCUSDT)")
    place_p.add_argument("--side",       required=True,  choices=["BUY", "SELL"], help="Order side")
    place_p.add_argument("--type",       required=True,  choices=["MARKET", "LIMIT", "STOP_MARKET"],
                         help="Order type")
    place_p.add_argument("--quantity",   required=True,  type=float, help="Order quantity")
    place_p.add_argument("--price",      default=None,   type=float,
                         help="Limit price (required for LIMIT orders)")
    place_p.add_argument("--stop-price", dest="stop_price", default=None, type=float,
                         help="Stop trigger price (required for STOP_MARKET)")
    place_p.add_argument("--tif",        default="GTC",  choices=["GTC", "IOC", "FOK"],
                         help="Time-in-force for LIMIT orders (default: GTC)")

    orders_p = sub.add_parser("orders", help="List open orders")
    orders_p.add_argument("--symbol", default=None, help="Filter by symbol (optional)")

    sub.add_parser("account", help="Show account balance summary")

    return parser


def main() -> None:
    parser = build_parser()
    args   = parser.parse_args()

    dispatch = {
        "ping":    cmd_ping,
        "place":   cmd_place,
        "orders":  cmd_orders,
        "account": cmd_account,
    }

    handler = dispatch.get(args.command)
    if handler:
        handler(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
