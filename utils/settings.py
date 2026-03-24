import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv


class Settings:
    """Configuration management class for loading and accessing config.json parameters."""

    def __init__(
        self,
        config_path: str = "config.json",
    ):
        """
        Initialize settings with configuration file.

        Args:
            config_path: Path to the configuration JSON file
        """
        self._config: Optional[Dict[str, Any]] = None

        self.config_path = config_path

        self._initialize_environment()
        self._load_config()
        self._load_exchanges()

    def _load_exchanges(self) -> None:
        """Load exchanges from config.json."""
        self._exchanges = self._config["exchanges_ws"]["exchanges"]

    def _initialize_environment(self) -> None:
        """Initialize environment variables from .env file."""
        env_file = Path(".env")

        # Load environment variables
        if env_file.exists():
            load_dotenv(env_file)
            print("[OK] Loaded environment variables from .env file")
        else:
            print("[WARNING] No .env file found. Using system environment variables.")

    def _load_config(self) -> None:
        """Load configuration from JSON file."""
        try:
            if not os.path.exists(self.config_path):
                raise FileNotFoundError(f"Configuration file {self.config_path} not found")

            with open(self.config_path, encoding="utf-8") as f:
                self._config = json.load(f)

            self._exchanges_symbols_path = self._config["_exchanges_symbols_path"]
            self._exchanges_symbols_trades_path = self._config["_exchanges_symbols_trades_path"]

            self._orders_path = self._config["_orders_path"]
            self._mock_data_path = self._config["_mock_data_path"]
            self._arbitrage_input_path = self._config["arbitrage_analyzer"]["input_file"]
            self._arbitrage_output_path = self._config["arbitrage_analyzer"]["output_file"]
            self._tokens_output_path = self._config["tokens_analyzer"]["output_path"]

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in configuration file: {e}") from e
        except Exception as e:
            raise RuntimeError(f"Error loading configuration: {e}") from e

    def reload_config(self) -> None:
        """Reload configuration from file."""
        self._load_config()

    def get_ccxt_credentials(self, ccxt_id: str) -> Dict[str, Any]:
        """Return API credentials for a ccxt exchange id from environment (.env).

        Supports multiple env var aliases and per-exchange prefixes as seen in .env-example:
          - <PREFIX>_API_KEY or <PREFIX>_KEY
          - <PREFIX>_SECRET or <PREFIX>_SECRET_KEY
          - <PREFIX>_PASSWORD or <PREFIX>_PASSPHRASE

        Example mappings:
          gateio -> GATE_*, binance -> BINANCE_*, okx -> OKX_*, coinbase -> COINBASE_*
        """
        id_to_prefix = {
            "binance": "BINANCE",
            "okx": "OKX",
            "bybit": "BYBIT",
            "gateio": "GATE",
            "bitget": "BITGET",
            "bingx": "BINGX",
            "mexc": "MEXC",
            "kraken": "KRAKEN",
            "coinbase": "COINBASE",
        }

        prefix = id_to_prefix.get(ccxt_id, ccxt_id.upper())

        # Read with aliases
        api_key = os.getenv(f"{prefix}_API_KEY") or os.getenv(f"{prefix}_KEY")
        secret = os.getenv(f"{prefix}_SECRET") or os.getenv(f"{prefix}_SECRET_KEY")
        password = os.getenv(f"{prefix}_PASSWORD") or os.getenv(f"{prefix}_PASSPHRASE")

        creds: Dict[str, Any] = {}
        if api_key:
            creds["apiKey"] = api_key
        if secret:
            creds["secret"] = secret
        if password:
            creds["password"] = password

        return creds

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key.

        Args:
            key: Configuration key (supports dot notation, e.g., 'symbols.spot')
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        if self._config is None:
            return default

        keys = key.split(".")
        value = self._config

        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    @property
    def symbols(self) -> list:
        """Get symbols array for both spot and futures trading."""
        with open(self._exchanges_symbols_path, "r") as f:
            exchanges_symbols = json.load(f)
        return exchanges_symbols["list"]

    # Arbitrage analyzer specific properties
    @property
    def arbitrage_input_file(self) -> str:
        """Get arbitrage analyzer input file path."""
        return self.get("arbitrage_analyzer.input_file", "data/last_prices_ws.json")

    @property
    def arbitrage_output_file(self) -> str:
        """Get arbitrage analyzer output file path."""
        return self.get("arbitrage_analyzer.output_file", "data/arbitrage_analysis.json")

    @property
    def arbitrage_interval(self) -> int:
        """Get arbitrage analyzer interval."""
        return self.get("arbitrage_analyzer.interval", 1)

    @property
    def arbitrage_volume_trade(self) -> float:
        """Get arbitrage analyzer volume trade."""
        return self.get("arbitrage_analyzer.volume_trade", 100.0)

    # Tokens analyzer specific properties
    @property
    def tokens_output_path(self) -> str:
        """Get tokens analyzer output path."""
        return self.get("tokens_analyzer.output_path", "data/tokens_analyzer.json")

    @property
    def tokens_test_mode(self) -> bool:
        """Get tokens analyzer test mode."""
        return self.get("tokens_analyzer.test_mode", False)

    @property
    def tokens_periods(self) -> Dict[str, str]:
        """Get tokens analyzer periods configuration."""
        return self.get(
            "tokens_analyzer.periods",
            {
                "delta": "1h",
                "vol": "1h",
                "trade": "1h",
                "NATR": "1h",
                "spread": "1h",
                "activity": "1h",
            },
        )

    @property
    def tokens_periods_seconds(self) -> Dict[str, int]:
        """Get tokens analyzer periods in seconds."""
        periods = self.tokens_periods
        result = {}
        for key, period in periods.items():
            if isinstance(period, int):
                result[key] = period
            elif isinstance(period, str):
                # Parse period string (e.g., "1h", "30m", "1d")
                if period.endswith("h"):
                    result[key] = int(period[:-1]) * 3600
                elif period.endswith("m"):
                    result[key] = int(period[:-1]) * 60
                elif period.endswith("d"):
                    result[key] = int(period[:-1]) * 86400
                else:
                    result[key] = 3600  # default 1 hour
            else:
                result[key] = 3600
        return result

    @property
    def tokens_thresholds(self) -> Dict[str, float]:
        """Get tokens analyzer thresholds configuration."""
        default_thresholds: Dict[str, float] = {
            "delta": 0.0,
            "vol": 0.0,
            "trade": 0.0,
            "NATR": 0.0,
            "spread": 0.0,
            "activity": 0.0,
        }
        return self.get("tokens_analyzer.thresholds", default_thresholds)

    @property
    def tokens_interval(self) -> int:
        """Get tokens analyzer interval."""
        return self.get("tokens_analyzer.interval", 60)

    @property
    def tokens_save_to_file(self) -> bool:
        """Get tokens analyzer save to file setting."""
        return self.get("tokens_analyzer.save_to_file", True)

    @property
    def exchanges_reconnect_interval(self) -> int:
        """Get exchanges reconnect interval."""
        return self.get("exchanges_ws.reconnect_interval", 5)

    @property
    def exchanges_max_reconnect_attempts(self) -> int:
        """Get exchanges max reconnect attempts."""
        return self.get("exchanges_ws.max_reconnect_attempts", 10)

    @property
    def exchanges_output_file(self) -> str:
        """Get exchanges output file path."""
        return self.get("exchanges_ws.output_file", "data/last_prices_ws.json")

    @property
    def ohlcv_timeframes(self) -> dict:
        """Get OHLCV timeframes configuration."""
        return self.get(
            "exchanges_ws.ohlcv_timeframes",
            {
                "5m": 6,
                "15m": 4,
                "1h": 2,
                "4h": 1,
                "1d": 1
            }
        )

    @property
    def ohlcv_timeframe_1m(self) -> bool:
        """Get 1m timeframe enabled setting."""
        return self.get("exchanges_ws.ohlcv_timeframe_1m", False)

    @property
    def ohlcv_timeframe_5m(self) -> bool:
        """Get 5m timeframe enabled setting."""
        return self.get("exchanges_ws.ohlcv_timeframe_5m", True)

    @property
    def max_symbols_for_trades(self) -> int:
        """Get maximum symbols to fetch for trades (None for all)."""
        return self.get("exchanges_ws.max_symbols_for_trades", None)

    @property
    def web_server(self) -> bool:
        """Get web server setting."""
        return self.get("web_server", False)

    @property
    def web_server_host(self) -> str:
        """Get web server host."""
        # Parse from web_server_address (e.g., "0.0.0.0:8000" -> "0.0.0.0")
        address = self.get("web_server_address", "0.0.0.0:8000")
        return str(address).split(":")[0]

    @property
    def web_server_port(self) -> int:
        """Get web server port."""
        # Parse from web_server_address (e.g., "0.0.0.0:8000" -> 8000)
        address = self.get("web_server_address", "0.0.0.0:8000")
        return int(str(address).split(":")[1])

    @property
    def web_server_address(self) -> str:
        """Get web server address."""
        result = self.get("web_server_address", "0.0.0.0:8000")
        return str(result)

    @property
    def desktop(self) -> bool:
        """Get desktop setting."""
        return self.get("desktop", False)

    @property
    def save_to_file(self) -> bool:
        """Get save to file setting."""
        return self.get("save_to_file", True)

    def __str__(self) -> str:
        """String representation of settings."""
        return f"Settings(config_path={self.config_path})"

    def __repr__(self) -> str:
        """Detailed representation of settings."""
        return f"Settings(config_path={self.config_path}, loaded={self._config is not None})"


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """
    Get the global settings instance.

    Returns:
        Settings instance
    """
    return settings


def reload_settings() -> None:
    """Reload the global settings from file."""
    settings.reload_config()
