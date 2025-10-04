import json
import os
from typing import Any, Dict, Optional


class Settings:
    """Configuration management class for loading and accessing config.json parameters."""

    def __init__(self, config_path: str = "config.json"):
        """
        Initialize settings with configuration file.

        Args:
            config_path: Path to the configuration JSON file
        """
        self.config_path = config_path
        self._config: Optional[Dict[str, Any]] = None
        self._load_config()

    def _load_config(self) -> None:
        """Load configuration from JSON file."""
        try:
            if not os.path.exists(self.config_path):
                raise FileNotFoundError(
                    f"Configuration file {self.config_path} not found"
                )

            with open(self.config_path, "r", encoding="utf-8") as f:
                self._config = json.load(f)

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in configuration file: {e}")
        except Exception as e:
            raise RuntimeError(f"Error loading configuration: {e}")

    def reload_config(self) -> None:
        """Reload configuration from file."""
        self._load_config()

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
    def symbols(self) -> Dict[str, str]:
        """Get trading symbols configuration."""
        return self.get("symbols", {})

    @property
    def spot_symbol(self) -> str:
        """Get spot trading symbol."""
        return self.get("symbols.spot", "BTC/USDT")

    @property
    def future_symbol(self) -> str:
        """Get futures trading symbol."""
        return self.get("symbols.future", "BTC/USDT:USDT")

    @property
    def arbitrage_config(self) -> Dict[str, Any]:
        """Get arbitrage analyzer configuration."""
        return self.get("arbitrage_analyzer", {})

    @property
    def tokens_config(self) -> Dict[str, Any]:
        """Get tokens analyzer configuration."""
        return self.get("tokens_analyzer", {})

    @property
    def exchanges_config(self) -> Dict[str, Any]:
        """Get exchanges WebSocket configuration."""
        return self.get("exchanges_ws", {})

    @property
    def logging_config(self) -> Dict[str, Any]:
        """Get logging configuration."""
        return self.get("logging", {})

    # Arbitrage analyzer specific properties
    @property
    def arbitrage_input_file(self) -> str:
        """Get arbitrage analyzer input file path."""
        return self.get("arbitrage_analyzer.input_file", "data/last_prices_ws.json")

    @property
    def arbitrage_output_file(self) -> str:
        """Get arbitrage analyzer output file path."""
        return self.get(
            "arbitrage_analyzer.output_file", "data/arbitrage_analysis.json"
        )

    @property
    def arbitrage_symbol(self) -> str:
        """Get arbitrage analyzer symbol."""
        return self.get("arbitrage_analyzer.symbol", "BTC/USDT:USDT")

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
    def tokens_thresholds(self) -> Dict[str, float]:
        """Get tokens analyzer thresholds configuration."""
        return self.get(
            "tokens_analyzer.thresholds",
            {"delta": 0, "vol": 0, "trade": 0, "NATR": 0, "spread": 0, "activity": 0},
        )

    @property
    def tokens_interval(self) -> int:
        """Get tokens analyzer interval."""
        return self.get("tokens_analyzer.interval", 60)

    # Exchanges WebSocket specific properties
    @property
    def exchanges_list(self) -> list:
        """Get list of exchanges for WebSocket connections."""
        return self.get("exchanges_ws.exchanges", ["binance", "okx", "bybit"])

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

    # Logging specific properties
    @property
    def log_level(self) -> str:
        """Get logging level."""
        return self.get("logging.level", "INFO")

    @property
    def log_format(self) -> str:
        """Get logging format."""
        return self.get(
            "logging.format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    @property
    def log_file(self) -> str:
        """Get logging file path."""
        return self.get("logging.file", "logs/log.log")

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
