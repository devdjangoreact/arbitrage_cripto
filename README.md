# Arbitrage Crypto Analysis System

A comprehensive cryptocurrency arbitrage detection and analysis system that monitors multiple exchanges in real-time to identify profitable trading opportunities.

## 🚀 Features

- **Real-time Data Streaming**: WebSocket connections to 9 major cryptocurrency exchanges
- **Arbitrage Detection**: Automatic identification of price differences across exchanges
- **Token Analysis**: Advanced metrics calculation for trading opportunities
- **Configurable Settings**: JSON-based configuration for all parameters
- **Environment Management**: Secure API key management with .env files
- **Comprehensive Logging**: Detailed logging and monitoring capabilities
- **Modular Architecture**: Clean, organized code structure with separate modules

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Installation](#installation)
- [Configuration](#configuration)
- [Environment Setup](#environment-setup)
- [Exchange Configuration](#exchange-configuration)
- [MCP Setup](#mcp-setup)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Project Structure](#project-structure)
- [Testing](#testing)
- [Security](#security)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

## 🚀 Quick Start

1. **Clone the repository:**

   ```bash
   git clone <repository-url>
   cd arbitrage_cripto
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Configure API keys:**

   ```bash
   # The .env file will be created automatically from .env-example
   # Edit .env file with your API keys
   nano .env
   ```

4. **Run the application:**
   ```bash
   python main.py
   ```

## 📦 Installation

### Prerequisites

- Python 3.8+
- pip package manager
- API keys from supported exchanges

### Dependencies

The project requires the following Python packages:

```
websockets
ccxt
protobuf==5.29.5
uv==0.8.22
ruff==0.13.3
python-dotenv
```

### Install from requirements.txt

```bash
pip install -r requirements.txt
```

### Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## ⚙️ Configuration

The system uses a JSON-based configuration file (`config.json`) for all settings:

```json
{
  "symbols": {
    "spot": "BTC/USDT",
    "future": "BTC/USDT:USDT"
  },
  "arbitrage_analyzer": {
    "input_file": "data/last_prices_ws.json",
    "output_file": "data/arbitrage_analysis.json",
    "symbol": "BTC/USDT:USDT",
    "interval": 1,
    "volume_trade": 100
  },
  "tokens_analyzer": {
    "output_path": "data/tokens_analyzer.json",
    "test_mode": false,
    "periods": {
      "delta": "1h",
      "vol": "4h",
      "trade": "1h",
      "NATR": "1d",
      "spread": "15m",
      "activity": "1h"
    },
    "thresholds": {
      "delta": 0,
      "vol": 0,
      "trade": 0,
      "NATR": 0,
      "spread": 0,
      "activity": 0
    },
    "interval": 5
  },
  "exchanges_ws": {
    "exchanges": ["binance", "okx", "bybit", "gate", "bitget", "bingx", "mexc"],
    "reconnect_interval": 5,
    "max_reconnect_attempts": 10,
    "output_file": "data/last_prices_ws.json"
  },
  "logging": {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": "logs/log.log"
  }
}
```

## 🔐 Environment Setup

### Quick Setup

1. **Run the application (creates .env automatically):**

   ```bash
   python main.py
   ```

2. **Edit with your API keys:**

   ```bash
   nano .env
   ```

3. **Run again to use your API keys:**
   ```bash
   python main.py
   ```

### Manual Setup

1. **Copy template:**

   ```bash
   cp .env-example .env
   ```

2. **Edit .env file with your API keys**

3. **Run the application:**
   ```bash
   python main.py
   ```

### Supported Exchanges

| Exchange     | API Key | Secret Key | Passphrase | Sandbox |
| ------------ | ------- | ---------- | ---------- | ------- |
| **Binance**  | ✅      | ✅         | ❌         | ✅      |
| **OKX**      | ✅      | ✅         | ✅         | ✅      |
| **Bybit**    | ✅      | ✅         | ❌         | ✅      |
| **Gate.io**  | ✅      | ✅         | ❌         | ✅      |
| **Bitget**   | ✅      | ✅         | ✅         | ✅      |
| **BingX**    | ✅      | ✅         | ❌         | ✅      |
| **MEXC**     | ✅      | ✅         | ❌         | ✅      |
| **Kraken**   | ✅      | ✅         | ❌         | ✅      |
| **Coinbase** | ✅      | ✅         | ✅         | ✅      |

### Environment Variables

#### Exchange API Keys

| Variable              | Description         | Required | Example        |
| --------------------- | ------------------- | -------- | -------------- |
| `BINANCE_API_KEY`     | Binance API key     | Yes\*    | `abc123...`    |
| `BINANCE_SECRET_KEY`  | Binance secret key  | Yes\*    | `def456...`    |
| `OKX_API_KEY`         | OKX API key         | Yes\*    | `ghi789...`    |
| `OKX_SECRET_KEY`      | OKX secret key      | Yes\*    | `jkl012...`    |
| `OKX_PASSPHRASE`      | OKX passphrase      | Yes\*    | `mypassphrase` |
| `BYBIT_API_KEY`       | Bybit API key       | Yes\*    | `mno345...`    |
| `BYBIT_SECRET_KEY`    | Bybit secret key    | Yes\*    | `pqr678...`    |
| `GATE_API_KEY`        | Gate.io API key     | Yes\*    | `stu901...`    |
| `GATE_SECRET_KEY`     | Gate.io secret key  | Yes\*    | `vwx234...`    |
| `BITGET_API_KEY`      | Bitget API key      | Yes\*    | `yza567...`    |
| `BITGET_SECRET_KEY`   | Bitget secret key   | Yes\*    | `bcd890...`    |
| `BITGET_PASSPHRASE`   | Bitget passphrase   | Yes\*    | `mypassphrase` |
| `BINGX_API_KEY`       | BingX API key       | Yes\*    | `efg123...`    |
| `BINGX_SECRET_KEY`    | BingX secret key    | Yes\*    | `hij456...`    |
| `MEXC_API_KEY`        | MEXC API key        | Yes\*    | `klm789...`    |
| `MEXC_SECRET_KEY`     | MEXC secret key     | Yes\*    | `nop012...`    |
| `KRAKEN_API_KEY`      | Kraken API key      | Yes\*    | `qrs345...`    |
| `KRAKEN_SECRET_KEY`   | Kraken secret key   | Yes\*    | `tuv678...`    |
| `COINBASE_API_KEY`    | Coinbase API key    | Yes\*    | `wxy901...`    |
| `COINBASE_SECRET_KEY` | Coinbase secret key | Yes\*    | `zab234...`    |
| `COINBASE_PASSPHRASE` | Coinbase passphrase | Yes\*    | `mypassphrase` |

\*Required only if you want to use that specific exchange

#### General Settings

| Variable                    | Description                            | Default | Example |
| --------------------------- | -------------------------------------- | ------- | ------- |
| `GLOBAL_SANDBOX`            | Enable sandbox mode for all exchanges  | `false` | `true`  |
| `RATE_LIMIT_PER_MINUTE`     | API rate limit (requests per minute)   | `60`    | `120`   |
| `WS_RECONNECT_INTERVAL`     | WebSocket reconnect interval (seconds) | `5`     | `10`    |
| `WS_MAX_RECONNECT_ATTEMPTS` | Max WebSocket reconnect attempts       | `10`    | `20`    |

## 🔄 Exchange Configuration

### How Exchange Initialization Works

The `exchanges_ws.py` file automatically initializes only the exchanges specified in `config.json`. Here's how it works:

1. **Reads from config.json**: Gets the `exchanges` array
2. **Initializes only these exchanges**: Creates instances only for exchanges in the config
3. **Ignores other exchanges**: Even though the code supports more exchanges, they won't be initialized because they're not in your config

### Changing Exchanges

To use different exchanges, simply modify the `exchanges` array in `config.json`:

#### Example 1: Use only major exchanges

```json
"exchanges": ["binance", "okx", "bybit"]
```

#### Example 2: Use all available exchanges

```json
"exchanges": ["binance", "okx", "bybit", "gate", "bitget", "bingx", "mexc", "kraken", "coinbase"]
```

#### Example 3: Use only specific exchanges

```json
"exchanges": ["binance", "mexc"]
```

### Testing Exchange Configuration

The application will automatically show which exchanges are initialized when you run it:

```bash
python main.py
```

This will show:

- Which exchanges are configured in `config.json`
- Which exchanges were actually initialized
- Any errors during initialization

## 🔧 MCP Setup

This project includes support for Model Context Protocol (MCP) integration with Cursor IDE for enhanced AI-powered mobile automation capabilities.

### Prerequisites

- Node.js installed on your system
- Cursor IDE
- Mobile device or emulator for testing

### Installation

1. **Install Appium MCP globally:**

   ```bash
   npm install -g appium-mcp
   ```

2. **Install Appium server:**

   ```bash
   npm install -g appium
   ```

3. **MCP Configuration is automatically set up:**

   The MCP configuration file has been created at:

   ```
   C:\Users\[username]\AppData\Roaming\Cursor\User\globalStorage\saoudrizwan.claude-dev\settings\cline_mcp_settings.json
   ```

### Mobile Device Setup

#### Android Setup

1. **Enable Developer Options:**

   - Go to Settings > About Phone
   - Tap "Build Number" 7 times
   - Go back to Settings > Developer Options
   - Enable "USB Debugging"

2. **Connect Device:**
   ```bash
   # Connect via USB or start emulator
   adb devices
   ```

#### iOS Setup (macOS only)

1. **Install Xcode command line tools:**

   ```bash
   xcode-select --install
   ```

2. **Set up iOS simulator or connect real device**

### Usage

1. **Start Appium server:**

   ```bash
   appium
   ```

2. **Restart Cursor IDE** to load the MCP configuration

3. **Use MCP features in Cursor:**
   - The Appium MCP server will be available for AI-powered mobile automation
   - You can now use natural language commands for mobile testing and automation

### Configuration

The MCP server is configured with the following settings:

```json
{
  "mcpServers": {
    "appium-mcp": {
      "command": "npx",
      "args": ["appium-mcp"],
      "autoApprove": [],
      "timeout": 300,
      "transportType": "stdio",
      "disabled": false
    }
  }
}
```

### Troubleshooting MCP

1. **MCP not working:**

   - Ensure Node.js is installed
   - Check if `appium-mcp` is installed globally
   - Restart Cursor IDE after configuration

2. **Device not detected:**

   - Check USB debugging is enabled (Android)
   - Verify device connection with `adb devices`
   - Ensure Appium server is running

3. **Configuration issues:**
   - Verify the MCP settings file exists in the correct location
   - Check file permissions and JSON syntax

## 📊 Usage

### Basic Usage

```python
import asyncio
from app.arbitrage_analyzer import AnalyzeArbitrage
from app.token_analyzer import TokensAnalyzer
from exchanges_ws import ExchangesWS
from logger import get_logger
from settings import get_settings

async def main():
    # Load configuration
    settings = get_settings()

    # Initialize components
    logger = get_logger()
    ws_exchanges = ExchangesWS(logger=logger)

    # Initialize analyzers
    analyzer = AnalyzeArbitrage(
        input_file=settings.arbitrage_input_file,
        output_file=settings.arbitrage_output_file,
        symbol=settings.arbitrage_symbol,
        interval=settings.arbitrage_interval,
        last_prices_collection=ws_exchanges.last_prices,
        volume_trade=settings.arbitrage_volume_trade,
    )

    tokens_analyzer = TokensAnalyzer(
        last_prices_collection=ws_exchanges.last_prices,
        output_path=settings.tokens_output_path,
        test_mode=settings.tokens_test_mode,
        periods=settings.tokens_periods,
        thresholds=settings.tokens_thresholds,
    )

    # Run the system
    await asyncio.gather(
        ws_exchanges.stream_futures(settings.spot_symbol, settings.future_symbol),
        analyzer.run(),
        tokens_analyzer.run(interval=settings.tokens_interval),
    )

if __name__ == "__main__":
    asyncio.run(main())
```

### TokensAnalyzer Usage

#### Basic Usage

```python
from app.token_analyzer import TokensAnalyzer

# Create analyzer
analyzer = TokensAnalyzer()

# Process data
analyzer.last_prices_collection = your_data_collection

# Calculate metrics for specific token
metrics = analyzer.calculate_metrics('binance', 'btc')

# Filter and save results
result = analyzer.filter_and_save()
```

#### Advanced Configuration

```python
# Custom periods
periods = {
    'delta': '1h',      # Delta over 1 hour
    'vol': '4h',        # Volume over 4 hours
    'trade': '1h',      # Trade count over 1 hour
    'NATR': '1d',       # NATR over 1 day
    'spread': '15m',    # Spread over 15 minutes
    'activity': '1h'    # Activity over 1 hour
}

# Custom thresholds
thresholds = {
    'delta': 0.001,     # 0.1% minimum price difference
    'vol': 1000,        # minimum trading volume
    'trade': 10,        # minimum number of trades
    'NATR': 0.01,       # minimum volatility
    'spread': 0.0001,   # minimum spread
    'activity': 0.1     # minimum activity
}

analyzer = TokensAnalyzer(
    periods=periods,
    thresholds=thresholds
)
```

## 📚 API Documentation

### TokensAnalyzer

The `TokensAnalyzer` class provides comprehensive token analysis for arbitrage opportunities.

#### Key Features

- **Delta Calculation**: Absolute price difference over time periods
- **Volume Analysis**: Total trading volume calculations
- **Trade Count**: Number of trades in specified periods
- **NATR (Normalized Average True Range)**: Volatility measurement
- **Spread Analysis**: Bid-ask spread calculations
- **Activity Metrics**: Price update frequency analysis

#### Supported Periods

- `1m` (1 minute)
- `5m` (5 minutes)
- `15m` (15 minutes)
- `1h` (1 hour)
- `4h` (4 hours)
- `1d` (1 day)

#### Data Structure

**Input Data Format:**

```python
{
    'exchange': 'binance',
    'symbol': 'BTC/USDT',
    'timestamp': 1640995200000,
    'ask': [50000.0, 1.5],  # [price, volume]
    'bid': [49999.0, 2.0]   # [price, volume]
}
```

**Output Data Format:**

```json
{
  "binance": {
    "btc": {
      "delta": 0.004000040000400004,
      "vol": 5.3,
      "trade": 3,
      "NATR": 0.0,
      "spread": 1.9920318725099602e-5,
      "activity": 0.0005555555555555556
    }
  }
}
```

### ArbitrageAnalyzer

The `ArbitrageAnalyzer` class detects arbitrage opportunities across exchanges.

#### Key Features

- **Real-time Analysis**: Continuous monitoring of price differences
- **Profit Calculation**: Automatic P&L calculations
- **Volume Optimization**: Maximum tradeable volume calculations
- **Data Persistence**: Results saved to JSON files

### ExchangesWS

The `ExchangesWS` class manages WebSocket connections to multiple exchanges.

#### Key Features

- **Multi-Exchange Support**: Connect to 9 major exchanges
- **Automatic Reconnection**: Robust error handling and reconnection
- **Configurable Exchanges**: Only initialize specified exchanges
- **Data Normalization**: Unified data format across exchanges

## 📁 Project Structure

```
arbitrage_cripto/
├── app/                          # Core application modules
│   ├── __init__.py              # Package initialization
│   ├── arbitrage_analyzer.py    # Arbitrage detection logic
│   └── token_analyzer.py        # Token analysis logic
├── data/                        # Data storage directory
│   ├── last_prices_ws.json     # WebSocket price data
│   ├── arbitrage_analysis.json # Arbitrage results
│   └── tokens_analyzer.json    # Token analysis results
├── logs/                        # Log files directory
│   └── log.log                 # Application logs
├── tests/                       # Test files
│   ├── simple_test.py          # Basic functionality tests
│   ├── test_tokens_analyzer.py # Token analyzer tests
│   └── test_tokens_analyzer_en.py # English version tests
├── main.py                     # Main application entry point
├── exchanges_ws.py             # WebSocket exchange manager
├── logger.py                   # Logging configuration
├── settings.py                 # Settings management
├── config.json                 # Main configuration file
├── .env-example                # Environment variables template
├── .env                        # Environment variables (create from template)
├── .gitignore                  # Git ignore rules
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
python tests/test_tokens_analyzer.py

# Run simple test
python tests/simple_test.py

# Run English version tests
python tests/test_tokens_analyzer_en.py
```

### Test Coverage

The test suite covers:

- Basic functionality testing
- Real data processing
- Different time periods
- Edge cases and error handling
- Configuration validation

### Test Data

Test data is automatically generated and includes:

- Multiple exchange scenarios
- Various time periods
- Different token types
- Edge cases (empty data, invalid data)

## 🔒 Security

### API Key Security

1. **Never commit .env files to version control**
2. **Use strong, unique passphrases**
3. **Enable API key encryption in production**
4. **Restrict IP addresses when possible**

### Best Practices

1. **API Key Permissions**:

   - Never enable "Withdraw" permissions unless absolutely necessary
   - Use "Read" and "Trade" permissions only
   - Regularly rotate your API keys
   - Monitor API key usage

2. **Network Security**:

   - Use VPN if trading from public networks
   - Enable IP whitelisting on exchanges
   - Monitor for suspicious activity
   - Use 2FA on exchange accounts

3. **Environment Security**:
   - Use different API keys for testing and production
   - Enable sandbox mode for testing
   - Monitor logs for unauthorized access

### Sandbox Testing

To test without using real funds:

1. **Enable sandbox mode:**

   ```bash
   GLOBAL_SANDBOX=true
   ```

2. **Or enable for specific exchanges:**

   ```bash
   BINANCE_SANDBOX=true
   OKX_SANDBOX=true
   ```

3. **Get sandbox API keys from each exchange**

4. **Test with small amounts first**

## 🛠️ Troubleshooting

### Common Issues

1. **"Invalid API Key" Error**

   - Check if API key is correct
   - Verify API key permissions
   - Ensure API key is not expired

2. **"Rate Limit Exceeded" Error**

   - Increase `RATE_LIMIT_PER_MINUTE`
   - Add delays between requests
   - Check exchange rate limits

3. **"Connection Timeout" Error**

   - Check internet connection
   - Verify exchange is online
   - Increase timeout settings

4. **"Insufficient Permissions" Error**
   - Check API key permissions
   - Enable required permissions
   - Verify account verification status

### Debug Mode

Enable debug mode for detailed logging:

```bash
# In .env file
LOG_LEVEL=DEBUG
DEBUG_MODE=true
VERBOSE_LOGGING=true
```

### Getting Help

- Check exchange API documentation
- Review application logs
- Test with sandbox mode first
- Contact exchange support if needed

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

1. Clone your fork
2. Create virtual environment
3. Install dependencies
4. Set up environment variables
5. Run tests to ensure everything works

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- [CCXT](https://github.com/ccxt/ccxt) - Cryptocurrency exchange trading library
- [WebSockets](https://websockets.readthedocs.io/) - WebSocket implementation
- All supported cryptocurrency exchanges for providing APIs

## 📞 Support

For support and questions:

- Create an issue in the repository
- Check the troubleshooting section
- Review the documentation

---

**⚠️ Disclaimer**: This software is for educational and research purposes only. Cryptocurrency trading involves substantial risk of loss. Use at your own risk.
