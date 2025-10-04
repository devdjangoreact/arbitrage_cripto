#!/usr/bin/env python3
"""
Environment Setup Script

This script helps users set up their environment variables for the arbitrage crypto project.
"""

import os
import sys
from pathlib import Path


def create_env_file():
    """Create .env file from .env-example if it doesn't exist."""
    env_file = Path(".env")
    env_example = Path(".env-example")

    if env_file.exists():
        print("✅ .env file already exists")
        return True

    if not env_example.exists():
        print("❌ .env-example file not found")
        return False

    try:
        # Copy .env-example to .env
        with open(env_example, "r", encoding="utf-8") as src:
            content = src.read()

        with open(env_file, "w", encoding="utf-8") as dst:
            dst.write(content)

        print("✅ Created .env file from .env-example")
        return True
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")
        return False


def check_env_file():
    """Check if .env file exists and has content."""
    env_file = Path(".env")

    if not env_file.exists():
        print("❌ .env file not found")
        return False

    try:
        with open(env_file, "r", encoding="utf-8") as f:
            content = f.read().strip()

        if not content:
            print("❌ .env file is empty")
            return False

        # Check for placeholder values
        placeholder_count = content.count("your_") + content.count("_here")
        if placeholder_count > 0:
            print(
                f"⚠️  .env file contains {placeholder_count} placeholder values that need to be replaced"
            )
            return False

        print("✅ .env file exists and appears to be configured")
        return True
    except Exception as e:
        print(f"❌ Error reading .env file: {e}")
        return False


def validate_exchange_keys():
    """Validate exchange API keys."""
    try:
        from env_loader import get_env_loader

        loader = get_env_loader()
        available_exchanges = loader.get_available_exchanges()

        if not available_exchanges:
            print("❌ No exchanges configured with valid API keys")
            return False

        print(f"✅ Found {len(available_exchanges)} configured exchanges:")
        for exchange in available_exchanges:
            print(f"   - {exchange}")

        return True
    except ImportError:
        print("❌ env_loader module not found")
        return False
    except Exception as e:
        print(f"❌ Error validating exchange keys: {e}")
        return False


def show_setup_instructions():
    """Show setup instructions to the user."""
    print("\n" + "=" * 60)
    print("ENVIRONMENT SETUP INSTRUCTIONS")
    print("=" * 60)
    print()
    print("1. Copy .env-example to .env:")
    print("   cp .env-example .env")
    print()
    print("2. Edit .env file with your actual API keys:")
    print("   nano .env  # or use your preferred editor")
    print()
    print("3. Get API keys from supported exchanges:")
    print("   - Binance: https://www.binance.com/")
    print("   - OKX: https://www.okx.com/")
    print("   - Bybit: https://www.bybit.com/")
    print("   - Gate.io: https://www.gate.io/")
    print("   - Bitget: https://www.bitget.com/")
    print("   - BingX: https://bingx.com/")
    print("   - MEXC: https://www.mexc.com/")
    print("   - Kraken: https://www.kraken.com/")
    print("   - Coinbase: https://pro.coinbase.com/")
    print()
    print("4. For detailed instructions, see README_ENV_SETUP.md")
    print()
    print("5. Test your configuration:")
    print("   python setup_env.py --validate")
    print()


def main():
    """Main function."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Environment setup for arbitrage crypto project"
    )
    parser.add_argument(
        "--create", action="store_true", help="Create .env file from .env-example"
    )
    parser.add_argument(
        "--validate", action="store_true", help="Validate environment configuration"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check if .env file exists and is configured",
    )
    parser.add_argument(
        "--instructions", action="store_true", help="Show setup instructions"
    )

    args = parser.parse_args()

    if args.create:
        create_env_file()
    elif args.validate:
        print("Validating environment configuration...")
        if check_env_file():
            validate_exchange_keys()
    elif args.check:
        check_env_file()
    elif args.instructions:
        show_setup_instructions()
    else:
        # Default behavior - show status and instructions
        print("Arbitrage Crypto - Environment Setup")
        print("=" * 40)

        # Check current status
        env_exists = check_env_file()

        if not env_exists:
            print("\nSetting up environment...")
            if create_env_file():
                print("\nNext steps:")
                show_setup_instructions()
        else:
            print("\nValidating configuration...")
            validate_exchange_keys()

        print("\nFor more options, run: python setup_env.py --help")


if __name__ == "__main__":
    main()
