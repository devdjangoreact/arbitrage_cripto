import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv


class Settings:
    """Configuration management class for loading and accessing config.json parameters."""

    def __init__(
        self,
        config_path: str = "utils/config.json",
        exchanges_path: str = "utils/exchange.json",
        symbols_path: str = "utils/symbols.json",
    ):
        """
        Initialize settings with configuration file.

        Args:
            config_path: Path to the configuration JSON file
        """
        self.config_path = config_path
        self.exchanges_path = exchanges_path
        self.symbols_path = symbols_path
        self._config: Optional[Dict[str, Any]] = None
        self._initialize_environment()
        self._load_config()
        self._load_exchanges()
        self._load_symbols()

    def _load_exchanges(self) -> None:
        """Load exchanges from exchange.json."""
        with open(self.exchanges_path, encoding="utf-8") as f:
            self._exchanges = json.load(f)

    def _load_symbols(self) -> None:
        """Load symbols from symbols.json."""
        with open(self.symbols_path, encoding="utf-8") as f:
            self._symbols = json.load(f)

    def _initialize_environment(self) -> None:
        """Initialize environment variables from .env file."""
        env_file = Path(".env")
        env_example = Path(".env-example")

        # Create .env file from .env-example if it doesn't exist
        if not env_file.exists() and env_example.exists():
            print("Creating .env file from .env-example...")
            with open(env_example, encoding="utf-8") as src:
                content = src.read()
            with open(env_file, "w", encoding="utf-8") as dst:
                dst.write(content)
            print("[OK] Created .env file from .env-example")
            print("[WARNING] Please edit .env file with your actual API keys before running the application")

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
        default_symbols = ["BTC/USDT", "ETH/USDT", "BTC/USDT:USDT", "ETH/USDT:USDT"]
        result = self.get("symbols", default_symbols)
        return result if isinstance(result, list) else default_symbols

    # Arbitrage analyzer specific properties
    @property
    def arbitrage_input_file(self) -> str:
        """Get arbitrage analyzer input file path."""
        result = self.get("arbitrage_analyzer.input_file", "data/last_prices_ws.json")
        return str(result)

    @property
    def arbitrage_output_file(self) -> str:
        """Get arbitrage analyzer output file path."""
        result = self.get("arbitrage_analyzer.output_file", "data/arbitrage_analysis.json")
        return str(result)

    @property
    def arbitrage_interval(self) -> int:
        """Get arbitrage analyzer interval."""
        result = self.get("arbitrage_analyzer.interval", 1)
        return int(result) if isinstance(result, (int, float, str)) else 1

    @property
    def arbitrage_volume_trade(self) -> float:
        """Get arbitrage analyzer volume trade."""
        result = self.get("arbitrage_analyzer.volume_trade", 100.0)
        return float(result) if isinstance(result, (int, float, str)) else 100.0

    # Tokens analyzer specific properties
    @property
    def tokens_output_path(self) -> str:
        """Get tokens analyzer output path."""
        result = self.get("tokens_analyzer.output_path", "data/tokens_analyzer.json")
        return str(result)

    @property
    def tokens_test_mode(self) -> bool:
        """Get tokens analyzer test mode."""
        result = self.get("tokens_analyzer.test_mode", False)
        return bool(result) if isinstance(result, (bool, int, str)) else False

    @property
    def tokens_periods(self) -> Dict[str, str]:
        """Get tokens analyzer periods configuration."""
        default_periods = {
            "delta": "1h",
            "vol": "1h",
            "trade": "1h",
            "NATR": "1h",
            "spread": "1h",
            "activity": "1h",
        }
        result = self.get("tokens_analyzer.periods", default_periods)
        return result if isinstance(result, dict) else default_periods

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
        result = self.get("tokens_analyzer.thresholds", default_thresholds)
        if isinstance(result, dict):
            # Ensure all values are float
            return {k: float(v) if isinstance(v, (int, float)) else 0.0 for k, v in result.items()}
        return default_thresholds

    @property
    def tokens_interval(self) -> int:
        """Get tokens analyzer interval."""
        result = self.get("tokens_analyzer.interval", 60)
        return int(result) if isinstance(result, (int, float, str)) else 60

    @property
    def tokens_save_to_file(self) -> bool:
        """Get tokens analyzer save to file setting."""
        result = self.get("tokens_analyzer.save_to_file", True)
        return bool(result) if isinstance(result, (bool, int, str)) else True

    # Exchanges WebSocket specific properties
    @property
    def exchanges_list(self) -> list:
        """Get list of exchanges for WebSocket connections."""
        default_exchanges = ["binance", "okx", "bybit"]
        result = self.get("exchanges_ws.exchanges", default_exchanges)
        return result if isinstance(result, list) else default_exchanges

    @property
    def exchanges_reconnect_interval(self) -> int:
        """Get exchanges reconnect interval."""
        result = self.get("exchanges_ws.reconnect_interval", 5)
        return int(result) if isinstance(result, (int, float, str)) else 5

    @property
    def exchanges_max_reconnect_attempts(self) -> int:
        """Get exchanges max reconnect attempts."""
        result = self.get("exchanges_ws.max_reconnect_attempts", 10)
        return int(result) if isinstance(result, (int, float, str)) else 10

    @property
    def exchanges_output_file(self) -> str:
        """Get exchanges output file path."""
        result = self.get("exchanges_ws.output_file", "data/last_prices_ws.json")
        return str(result)

    @property
    def web_server(self) -> bool:
        """Get web server setting."""
        result = self.get("web_server", False)
        return bool(result) if isinstance(result, (bool, int, str)) else False

    @property
    def web_server_host(self) -> str:
        """Get web server host."""
        result = self.get("web_server_host", "0.0.0.0")
        return str(result)

    @property
    def web_server_port(self) -> int:
        """Get web server port."""
        result = self.get("web_server_port", 8000)
        return int(result) if isinstance(result, (int, float, str)) else 8000

    @property
    def desktop(self) -> bool:
        """Get desktop setting."""
        result = self.get("desktop", False)
        return bool(result) if isinstance(result, (bool, int, str)) else False

    @property
    def mexc_id(self) -> str:
        """Get MEXC ID from environment."""
        result = os.getenv("MEXC_API_KEY", "")
        return str(result)

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
