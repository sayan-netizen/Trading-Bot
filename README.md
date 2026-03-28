# 📈 Binance Futures Testnet Trading Bot

A clean, structured Python CLI application for placing orders on the **Binance USDT-M Futures Testnet**. Built with pure `requests` — no third-party Binance SDK required.

---

## Features

| Capability | Detail |
|---|---|
| Order types | `MARKET`, `LIMIT`, `STOP_MARKET` (bonus) |
| Order sides | `BUY`, `SELL` |
| CLI interface | `argparse` sub-commands with `--help` |
| Input validation | Dedicated `validators.py` with descriptive error messages |
| Structured logging | Timestamped file (DEBUG) + console (INFO) handlers |
| Error handling | API errors, network failures, and invalid input all handled cleanly |
| Account info | `account` sub-command shows wallet balance |
| Open orders | `orders` sub-command lists open positions |
| Connectivity check | `ping` sub-command |

---

## Project Structure

```
trading_bot/
├── bot/
│   ├── __init__.py
│   ├── client.py          # Binance REST client (HMAC signing, requests, error mapping)
│   ├── orders.py          # Order placement logic + response formatting
│   ├── validators.py      # Input validation (symbol, side, qty, price, etc.)
│   └── logging_config.py  # Shared logger factory
├── cli.py                 # CLI entry point (argparse sub-commands)
├── logs/
│   ├── market_order_sample.log
│   └── limit_order_sample.log
├── .env.example           # Credential template — copy to .env and fill in keys
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/trading-bot.git
cd trading-bot
```

### 2. Create a virtual environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure API credentials

```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

Open `.env` and fill in your Binance Futures Testnet credentials:

```
BINANCE_API_KEY=your_testnet_api_key_here
BINANCE_API_SECRET=your_testnet_api_secret_here
BINANCE_BASE_URL=https://testnet.binancefuture.com
```

> ⚠️ **Never commit `.env` to version control.** It is already listed in `.gitignore`.

#### Getting Testnet Credentials

1. Visit [https://testnet.binancefuture.com](https://testnet.binancefuture.com)
2. Log in with GitHub or Google
3. Go to **API Management → Generate HMAC Key**
4. Copy the **API Key** and **Secret Key** into your `.env` file

> ⚠️ The secret is shown only once — copy it immediately.

---

## Usage

### Check connectivity
```bash
python cli.py ping
```

### View account balance
```bash
python cli.py account
```

### Place a MARKET order
```bash
python cli.py place --symbol BTCUSDT --side BUY --type MARKET --quantity 0.002
```

### Place a LIMIT order
```bash
python cli.py place --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.002 --price 85000
```

### Place a STOP_MARKET order (bonus)
```bash
# SELL stop — stop price must be below current market price
python cli.py place --symbol BTCUSDT --side SELL --type STOP_MARKET --quantity 0.002 --stop-price 70000

# BUY stop — stop price must be above current market price
python cli.py place --symbol BTCUSDT --side BUY --type STOP_MARKET --quantity 0.002 --stop-price 95000
```

### View open orders
```bash
python cli.py orders
python cli.py orders --symbol BTCUSDT
```

### Get help
```bash
python cli.py --help
python cli.py place --help
```

---

## Example Output

### MARKET order

```
┌──────────────────────────────────────────────┐
│             ORDER REQUEST SUMMARY            │
├──────────────────────────────────────────────┤
│  Symbol     : BTCUSDT                        │
│  Side       : BUY                            │
│  Type       : MARKET                         │
│  Quantity   : 0.002                          │
│  Price      : N/A (MARKET)                   │
│  Stop Price : —                              │
└──────────────────────────────────────────────┘

╔══════════════════════════════════════════════╗
║           ORDER RESPONSE SUMMARY             ║
╚══════════════════════════════════════════════╝
  Order ID      : 4008583818
  Symbol        : BTCUSDT
  Side          : BUY
  Type          : MARKET
  Status        : FILLED
  Orig Qty      : 0.002
  Executed Qty  : 0.002
  Avg Fill Price : 85342.10000
──────────────────────────────────────────────
  ✅  Order placed successfully!
```

### LIMIT order

```
┌──────────────────────────────────────────────┐
│             ORDER REQUEST SUMMARY            │
├──────────────────────────────────────────────┤
│  Symbol     : BTCUSDT                        │
│  Side       : SELL                           │
│  Type       : LIMIT                          │
│  Quantity   : 0.002                          │
│  Price      : 85000                          │
│  Stop Price : —                              │
└──────────────────────────────────────────────┘

╔══════════════════════════════════════════════╗
║           ORDER RESPONSE SUMMARY             ║
╚══════════════════════════════════════════════╝
  Order ID      : 1920847361
  Symbol        : BTCUSDT
  Side          : SELL
  Type          : LIMIT
  Status        : NEW
  Orig Qty      : 0.002
  Executed Qty  : 0
  Limit Price   : 85000
  Time-in-Force : GTC
──────────────────────────────────────────────
  ✅  Order placed successfully!
```

---

## Logging

Every run creates a new timestamped log file under `logs/`:

```
logs/cli_YYYYMMDD_HHMMSS.log
logs/binance_client_YYYYMMDD_HHMMSS.log
```

- **File handler** — `DEBUG` and above: full request params, raw API responses, errors
- **Console handler** — `INFO` and above: human-readable progress only
- **Signatures are never logged** — redacted from all debug output for security

Sample log files are included in `logs/` from real testnet runs.

---

## Error Handling

| Scenario | Behaviour |
|---|---|
| Missing API credentials | Clear message printed, exits with code 1 |
| Invalid input (bad side, missing price, etc.) | `ValueError` caught, message printed, exits code 2 |
| API error (bad symbol, insufficient margin, etc.) | `BinanceClientError` with Binance error code printed, exits code 3 |
| Network timeout | Mapped to `BinanceClientError`, GET requests auto-retried 3× |
| DNS / connection failure | Caught and reported with a clear message |

---

## Assumptions

1. Targets **USDT-M Futures Testnet** only. Switch to mainnet by changing `BINANCE_BASE_URL` in `.env`.
2. **One-way mode** only (no hedge mode). All orders use `positionSide=BOTH`.
3. Minimum order value on testnet is **100 USDT**. Use `quantity=0.002` or more for BTCUSDT.
4. `STOP_MARKET` orders are routed to Binance's `/fapi/v1/algoOrder` endpoint with `algoType=CONDITIONAL` — required as of the Binance testnet migration in late 2025.
5. For `STOP_MARKET` SELL orders, `--stop-price` must be **below** current market price. For BUY, it must be **above**.
6. `python-binance` SDK is not used — all HTTP calls are made directly via `requests` for full transparency.

---

## Dependencies

```
requests>=2.31.0
urllib3>=2.0.0
python-dotenv>=1.0.0
```

---

## License

MIT
