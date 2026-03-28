# 📈 Binance Futures Testnet Trading Bot

A clean, structured Python CLI application for placing orders on the **Binance USDT-M Futures Testnet**.

---

## Features

| Capability | Detail |
|---|---|
| Order types | `MARKET`, `LIMIT`, `STOP_MARKET` (bonus) |
| Order sides | `BUY`, `SELL` |
| CLI interface | `argparse` with sub-commands and `--help` |
| Input validation | Dedicated `validators.py` with descriptive error messages |
| Structured logging | Separate file (DEBUG) + console (INFO) handlers, timestamped log files |
| Error handling | `BinanceClientError` for API errors, `ValueError` for bad input, `requests` exceptions for network failures |
| Account info | `account` sub-command shows wallet balance |
| Open orders | `orders` sub-command lists open positions |
| Connectivity check | `ping` sub-command |

---

## Project Structure

```
trading_bot/
├── bot/
│   ├── __init__.py
│   ├── client.py          # Binance REST client (signing, requests, error mapping)
│   ├── orders.py          # Order placement logic + response formatting
│   ├── validators.py      # Input validation (symbol, side, qty, price, etc.)
│   └── logging_config.py  # Shared logger factory
├── cli.py                 # CLI entry point (argparse sub-commands)
├── logs/
│   ├── market_order_sample.log
│   └── limit_order_sample.log
├── .env.example           # Credential template
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Setup

### 1. Clone / download the project

```bash
git clone https://github.com/<your-username>/binance-futures-bot.git
cd binance-futures-bot
```

### 2. Create a virtual environment

```bash
python -m venv .venv
# macOS / Linux
source .venv/bin/activate
# Windows
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure API credentials

```bash
cp .env.example .env
```

Edit `.env` and add your **Binance Futures Testnet** credentials:

```
BINANCE_API_KEY=your_testnet_api_key_here
BINANCE_API_SECRET=your_testnet_api_secret_here
BINANCE_BASE_URL=https://testnet.binancefuture.com   # optional, this is the default
```

> ⚠️ **Never commit `.env` to version control.** It's already listed in `.gitignore`.

#### Getting Testnet Credentials

1. Visit [https://testnet.binancefuture.com](https://testnet.binancefuture.com)
2. Log in (GitHub OAuth is supported)
3. Navigate to **API Management** → **Create API Key**
4. Copy the key and secret into your `.env` file

---

## Usage

### Check connectivity

```bash
python cli.py ping
```

### Place a MARKET order

```bash
python cli.py place --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
```

### Place a LIMIT order

```bash
python cli.py place --symbol ETHUSDT --side SELL --type LIMIT --quantity 0.01 --price 3200
```

### Place a STOP_MARKET order (bonus order type)

```bash
python cli.py place --symbol BTCUSDT --side SELL --type STOP_MARKET --quantity 0.001 --stop-price 55000
```

### View open orders

```bash
python cli.py orders
python cli.py orders --symbol BTCUSDT
```

### View account balance

```bash
python cli.py account
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
│  Quantity   : 0.001                          │
│  Price      : N/A (MARKET)                   │
│  Stop Price : —                              │
└──────────────────────────────────────────────┘

╔══════════════════════════════════════════════╗
║           ORDER RESPONSE SUMMARY             ║
╚══════════════════════════════════════════════╝
  Order ID      : 4008583818
  Client OID    : iFHhMUMiCVKibHOipjH9N3
  Symbol        : BTCUSDT
  Side          : BUY
  Type          : MARKET
  Status        : FILLED
  Orig Qty      : 0.001
  Executed Qty  : 0.001
  Avg Fill Price : 65782.40000
──────────────────────────────────────────────
  ✅  Order placed successfully!
```

### LIMIT order

```
┌──────────────────────────────────────────────┐
│             ORDER REQUEST SUMMARY            │
├──────────────────────────────────────────────┤
│  Symbol     : ETHUSDT                        │
│  Side       : SELL                           │
│  Type       : LIMIT                          │
│  Quantity   : 0.01                           │
│  Price      : 3200.0                         │
│  Stop Price : —                              │
└──────────────────────────────────────────────┘

╔══════════════════════════════════════════════╗
║           ORDER RESPONSE SUMMARY             ║
╚══════════════════════════════════════════════╝
  Order ID      : 1920847361
  Client OID    : web_c5Jkq82QVRizUNIa3WnX
  Symbol        : ETHUSDT
  Side          : SELL
  Type          : LIMIT
  Status        : NEW
  Orig Qty      : 0.01
  Executed Qty  : 0
  Limit Price   : 3200
  Time-in-Force : GTC
──────────────────────────────────────────────
  ✅  Order placed successfully!
```

---

## Logging

Every run appends to a new timestamped file under `logs/`:

```
logs/trading_bot_YYYYMMDD_HHMMSS.log
```

- **File handler** — captures `DEBUG` and above: full request params, raw API responses, errors
- **Console handler** — captures `INFO` and above: human-readable progress messages
- **Signature is never logged** (redacted from debug output for security)

Sample log files from real testnet runs are included in `logs/`:
- `market_order_sample.log` — BUY MARKET 0.001 BTCUSDT (FILLED)
- `limit_order_sample.log` — SELL LIMIT 0.01 ETHUSDT @ 3200 (NEW)

---

## Error Handling

| Scenario | Behaviour |
|---|---|
| Missing API credentials | Prints clear message, exits with code 1 |
| Invalid CLI input (bad side, missing price, etc.) | `ValueError` caught, printed, exits with code 2 |
| API error (e.g. insufficient margin, bad symbol) | `BinanceClientError` caught, Binance error code + message printed, exits code 3 |
| Network timeout | `requests.Timeout` mapped to `BinanceClientError`, retried for `GET` (3×) |
| Non-JSON response | `BinanceClientError` with raw text excerpt |

---

## Assumptions

1. The bot targets **USDT-M Futures Testnet** exclusively. Mainnet requires only changing `BINANCE_BASE_URL`.
2. **Hedge-mode** is not supported; all orders use `positionSide=BOTH` (one-way mode, the testnet default).
3. Quantity precision is passed as-is. If Binance returns a filter error (LOT_SIZE), round your quantity to match the symbol's `stepSize`.
4. The STOP_MARKET order triggers when the mark price crosses `--stop-price`; it then closes at market.
5. `python-binance` library is **not** used — all API calls are made via `requests` for full transparency and control.

---

## Dependencies

```
requests>=2.31.0
urllib3>=2.0.0
python-dotenv>=1.0.0
```

No third-party Binance SDK is required.

---

## License

MIT
