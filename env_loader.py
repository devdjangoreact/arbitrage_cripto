"""
Environment Variables Loader

This module provides utilities for loading and managing environment variables
for the arbitrage crypto project.
"""

import os
from typing import Any, Dict, Optional

from dotenv import load_dotenv


class EnvLoader:
    """Environment variables loader and manager."""

    def __init__(self, env_file: str = ".env"):
        """
        Initialize the environment loader.

        Args:
            env_file: Path to the environment file
        """
        self.env_file = env_file
        self._load_env()

    def _load_env(self) -> None:
        """Load environment variables from file."""
        if os.path.exists(self.env_file):
            load_dotenv(self.env_file)
        else:
            print(
                f"Warning: {self.env_file} not found. Using system environment variables."
            )

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get an environment variable.

        Args:
            key: Environment variable name
            default: Default value if not found

        Returns:
            Environment variable value or default
        """
        return os.getenv(key, default)

    def get_bool(self, key: str, default: bool = False) -> bool:
        """
        Get a boolean environment variable.

        Args:
            key: Environment variable name
            default: Default value if not found

        Returns:
            Boolean value
        """
        value = self.get(key, str(default)).lower()
        return value in ("true", "1", "yes", "on")

    def get_int(self, key: str, default: int = 0) -> int:
        """
        Get an integer environment variable.

        Args:
            key: Environment variable name
            default: Default value if not found

        Returns:
            Integer value
        """
        try:
            return int(self.get(key, str(default)))
        except (ValueError, TypeError):
            return default

    def get_float(self, key: str, default: float = 0.0) -> float:
        """
        Get a float environment variable.

        Args:
            key: Environment variable name
            default: Default value if not found

        Returns:
            Float value
        """
        try:
            return float(self.get(key, str(default)))
        except (ValueError, TypeError):
            return default

    def get_exchange_config(self, exchange: str) -> Dict[str, str]:
        """
        Get configuration for a specific exchange.

        Args:
            exchange: Exchange name (e.g., 'binance', 'okx')

        Returns:
            Dictionary with exchange configuration
        """
        exchange = exchange.upper()
        config = {}

        # Common keys for all exchanges
        api_key = self.get(f"{exchange}_API_KEY")
        secret_key = self.get(f"{exchange}_SECRET_KEY")

        if api_key:
            config["apiKey"] = api_key
        if secret_key:
            config["secret"] = secret_key

        # Exchange-specific keys
        if exchange in ["OKX", "BITGET", "COINBASE"]:
            passphrase = self.get(f"{exchange}_PASSPHRASE")
            if passphrase:
                config["password"] = passphrase

        # Sandbox/testnet settings
        sandbox_key = f"{exchange}_SANDBOX"
        if exchange == "BYBIT":
            sandbox_key = f"{exchange}_TESTNET"

        sandbox = self.get_bool(sandbox_key)
        if sandbox:
            config["sandbox"] = True
            config["testnet"] = True

        return config

    def get_all_exchange_configs(self) -> Dict[str, Dict[str, str]]:
        """
        Get configuration for all exchanges.

        Returns:
            Dictionary with all exchange configurations
        """
        exchanges = [
            "binance",
            "okx",
            "bybit",
            "gate",
            "bitget",
            "bingx",
            "mexc",
            "kraken",
            "coinbase",
        ]

        configs = {}
        for exchange in exchanges:
            config = self.get_exchange_config(exchange)
            if config:  # Only include exchanges with configuration
                configs[exchange] = config

        return configs

    def get_general_settings(self) -> Dict[str, Any]:
        """
        Get general application settings.

        Returns:
            Dictionary with general settings
        """
        return {
            "global_sandbox": self.get_bool("GLOBAL_SANDBOX", False),
            "rate_limit_per_minute": self.get_int("RATE_LIMIT_PER_MINUTE", 60),
            "ws_reconnect_interval": self.get_int("WS_RECONNECT_INTERVAL", 5),
            "ws_max_reconnect_attempts": self.get_int("WS_MAX_RECONNECT_ATTEMPTS", 10),
            "log_level": self.get("LOG_LEVEL", "INFO"),
            "log_file": self.get("LOG_FILE", "logs/arbitrage.log"),
            "data_directory": self.get("DATA_DIRECTORY", "data"),
            "backup_enabled": self.get_bool("BACKUP_ENABLED", True),
            "backup_interval_hours": self.get_int("BACKUP_INTERVAL_HOURS", 24),
            "debug_mode": self.get_bool("DEBUG_MODE", False),
            "verbose_logging": self.get_bool("VERBOSE_LOGGING", False),
            "mock_exchanges": self.get_bool("MOCK_EXCHANGES", False),
        }

    def get_security_settings(self) -> Dict[str, Any]:
        """
        Get security-related settings.

        Returns:
            Dictionary with security settings
        """
        return {
            "encrypt_api_keys": self.get_bool("ENCRYPT_API_KEYS", False),
            "encryption_key": self.get("ENCRYPTION_KEY"),
            "allowed_ips": (
                self.get("ALLOWED_IPS", "").split(",")
                if self.get("ALLOWED_IPS")
                else []
            ),
        }

    def get_notification_settings(self) -> Dict[str, Any]:
        """
        Get notification settings.

        Returns:
            Dictionary with notification settings
        """
        return {
            "telegram_bot_token": self.get("TELEGRAM_BOT_TOKEN"),
            "telegram_chat_id": self.get("TELEGRAM_CHAT_ID"),
            "smtp_server": self.get("SMTP_SERVER"),
            "smtp_port": self.get_int("SMTP_PORT", 587),
            "smtp_username": self.get("SMTP_USERNAME"),
            "smtp_password": self.get("SMTP_PASSWORD"),
            "notification_email": self.get("NOTIFICATION_EMAIL"),
        }

    def get_arbitrage_settings(self) -> Dict[str, Any]:
        """
        Get arbitrage-specific settings.

        Returns:
            Dictionary with arbitrage settings
        """
        return {
            "min_arbitrage_profit": self.get_float("MIN_ARBITRAGE_PROFIT", 0.001),
            "max_arbitrage_volume": self.get_float("MAX_ARBITRAGE_VOLUME", 1000.0),
            "arbitrage_timeout_seconds": self.get_int("ARBITRAGE_TIMEOUT_SECONDS", 30),
        }

    def validate_required_keys(self, exchange: str) -> bool:
        """
        Validate that required API keys are present for an exchange.

        Args:
            exchange: Exchange name

        Returns:
            True if all required keys are present
        """
        exchange = exchange.upper()

        # Check for API key and secret
        api_key = self.get(f"{exchange}_API_KEY")
        secret_key = self.get(f"{exchange}_SECRET_KEY")

        if not api_key or not secret_key:
            return False

        # Check for passphrase if required
        if exchange in ["OKX", "BITGET", "COINBASE"]:
            passphrase = self.get(f"{exchange}_PASSPHRASE")
            if not passphrase:
                return False

        return True

    def get_available_exchanges(self) -> list:
        """
        Get list of exchanges with valid configuration.

        Returns:
            List of exchange names with valid configuration
        """
        exchanges = [
            "binance",
            "okx",
            "bybit",
            "gate",
            "bitget",
            "bingx",
            "mexc",
            "kraken",
            "coinbase",
        ]

        available = []
        for exchange in exchanges:
            if self.validate_required_keys(exchange):
                available.append(exchange)

        return available


# Global environment loader instance
env_loader = EnvLoader()


def get_env_loader() -> EnvLoader:
    """
    Get the global environment loader instance.

    Returns:
        EnvLoader instance
    """
    return env_loader


def load_exchange_config(exchange: str) -> Dict[str, str]:
    """
    Load configuration for a specific exchange.

    Args:
        exchange: Exchange name

    Returns:
        Exchange configuration dictionary
    """
    return env_loader.get_exchange_config(exchange)


def load_all_exchange_configs() -> Dict[str, Dict[str, str]]:
    """
    Load configuration for all exchanges.

    Returns:
        Dictionary with all exchange configurations
    """
    return env_loader.get_all_exchange_configs()


def get_available_exchanges() -> list:
    """
    Get list of available exchanges.

    Returns:
        List of exchange names with valid configuration
    """
    return env_loader.get_available_exchanges()


# Example usage
if __name__ == "__main__":
    # Load environment variables
    loader = EnvLoader()

    # Get general settings
    general_settings = loader.get_general_settings()
    print("General Settings:", general_settings)

    # Get available exchanges
    available_exchanges = loader.get_available_exchanges()
    print("Available Exchanges:", available_exchanges)

    # Get configuration for a specific exchange
    if available_exchanges:
        exchange_config = loader.get_exchange_config(available_exchanges[0])
        print(f"Configuration for {available_exchanges[0]}:", exchange_config)
