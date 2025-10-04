import asyncio
import json
from datetime import datetime

import ccxt.pro as ccxtpro

from settings import get_settings


class ExchangesWS:

    def __init__(self, logger=None, last_prices_file=None):
        # Load settings
        self.settings = get_settings()

        # Set logger first
        self.logger = logger

        # Use settings for configuration
        self.last_prices_file = last_prices_file or self.settings.arbitrage_input_file

        # Initialize exchanges based on settings
        self.exchanges = self._initialize_exchanges()

        self.last_prices = []
        self._load_last_prices()

    def _initialize_exchanges(self):
        """Initialize exchanges based on settings configuration."""
        exchanges = {}

        # Get list of exchanges from settings
        exchange_list = self.settings.exchanges_list

        # Map exchange names to ccxt.pro instances
        exchange_map = {
            "binance": ccxtpro.binance,
            "okx": ccxtpro.okx,
            "bybit": ccxtpro.bybit,
            "gate": ccxtpro.gateio,
            "bitget": ccxtpro.bitget,
            "bingx": ccxtpro.bingx,
            "mexc": ccxtpro.mexc,
            "kraken": ccxtpro.kraken,
            "coinbase": ccxtpro.coinbase,
        }

        # Initialize only the exchanges specified in settings
        for exchange_name in exchange_list:
            if exchange_name in exchange_map:
                try:
                    exchanges[exchange_name] = exchange_map[exchange_name]()
                    if self.logger:
                        self.logger.info(f"Initialized exchange: {exchange_name}")
                except Exception as e:
                    if self.logger:
                        self.logger.error(
                            f"Failed to initialize exchange {exchange_name}: {e}"
                        )
            else:
                if self.logger:
                    self.logger.warning(f"Unknown exchange: {exchange_name}")

        return exchanges

    def _load_last_prices(self):
        try:
            with open(self.last_prices_file, "r", encoding="utf-8") as f:
                loaded = []
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        obj = json.loads(line)
                        # Add only if it's a dict and has no 'error' field
                        if isinstance(obj, dict) and "error" not in obj:
                            loaded.append(obj)
                    except Exception:
                        continue
                self.last_prices = loaded
        except Exception:
            self.last_prices = []

    async def stream_futures(
        self,
        spot_symbol: str,
        future_symbol: str,
        output_file: str = None,
    ):
        # Use settings for output file if not provided
        if output_file is None:
            output_file = self.settings.exchanges_output_file

        async def symbol_loop(exchange, symbol, label):
            reconnect_attempts = 0
            max_reconnect_attempts = self.settings.exchanges_max_reconnect_attempts
            reconnect_interval = self.settings.exchanges_reconnect_interval

            while reconnect_attempts < max_reconnect_attempts:
                try:
                    orderbook = await exchange.watch_order_book(symbol)
                    entry = {
                        "exchange": exchange.id,
                        "symbol": symbol,
                        "label": label,
                        "timestamp": orderbook["timestamp"],
                        "datetime": orderbook["datetime"],
                        "ask": orderbook["asks"][0] if orderbook["asks"] else None,
                        "bid": orderbook["bids"][0] if orderbook["bids"] else None,
                    }
                    norm_entry = self.normalize_last_price_entry(entry)
                    if self.logger:
                        self.logger.info(f"{norm_entry}")
                    # Add to collection only if dict
                    if isinstance(norm_entry, dict):
                        self.last_prices.append(norm_entry)
                    # Add to file
                    with open(output_file, "a", encoding="utf-8") as f:
                        f.write(json.dumps(norm_entry, ensure_ascii=False) + "\n")

                    # Reset reconnect attempts on successful connection
                    reconnect_attempts = 0

                except Exception as e:
                    reconnect_attempts += 1
                    err_entry = {
                        "error": str(e),
                        "exchange": exchange.id,
                        "symbol": symbol,
                        "label": label,
                        "timestamp": datetime.utcnow().isoformat(),
                        "reconnect_attempt": reconnect_attempts,
                    }
                    if self.logger:
                        self.logger.error(f"{err_entry}")
                    with open(output_file, "a", encoding="utf-8") as f:
                        f.write(json.dumps(err_entry) + "\n")

                    if reconnect_attempts < max_reconnect_attempts:
                        if self.logger:
                            self.logger.info(
                                f"Reconnecting {exchange.id} in {reconnect_interval} seconds... (attempt {reconnect_attempts}/{max_reconnect_attempts})"
                            )
                        await asyncio.sleep(reconnect_interval)
                    else:
                        if self.logger:
                            self.logger.error(
                                f"Max reconnection attempts reached for {exchange.id}. Stopping."
                            )
                        break

        tasks = []
        for name, ex in self.exchanges.items():
            tasks.append(symbol_loop(ex, spot_symbol, f"spot_{name}"))
            tasks.append(symbol_loop(ex, future_symbol, f"future_{name}"))
        await asyncio.gather(*tasks)
        for ex in self.exchanges.values():
            await ex.close()

    def normalize_last_price_entry(self, entry):
        # Normalize entry to unified format for last_prices_ws.json
        norm = {
            "exchange": entry.get("exchange"),
            "symbol": entry.get("symbol"),
            "label": entry.get("label"),
            "timestamp": int(entry.get("timestamp", 0)),
            "datetime": entry.get("datetime"),
            "ask": None,
            "bid": None,
        }
        # ask and bid are arrays of two numbers: [price, volume]
        ask = entry.get("ask")
        bid = entry.get("bid")

        def to_price_volume(val):
            if isinstance(val, (list, tuple)) and len(val) >= 2:
                return [float(val[0]), float(val[1])]
            if isinstance(val, dict):
                return [float(val.get("price", 0)), float(val.get("amount", 0))]
            if isinstance(val, (int, float)):
                return [float(val), 0.0]
            return None

        norm["ask"] = to_price_volume(ask) if ask else None
        norm["bid"] = to_price_volume(bid) if bid else None
        return norm

    async def create_closing_changing_order(
        self,
        symbol: str,
        side: str,
        amount: float,
        price: float = None,
        order_type: str = "market",
        exchange_name: str = None,
        **kwargs,
    ):
        """
        Create a closing changing order on specified exchange or all exchanges.

        Args:
            symbol (str): Trading symbol (e.g., 'BTC/USDT')
            side (str): Order side ('buy' or 'sell')
            amount (float): Order amount
            price (float, optional): Order price for limit orders
            order_type (str): Order type ('market', 'limit', 'stop', 'stop_limit')
            exchange_name (str, optional): Specific exchange name. If None, tries all exchanges
            **kwargs: Additional parameters for order creation

        Returns:
            dict: Results from each exchange with order details or errors
        """
        results = {}

        # Determine which exchanges to use
        target_exchanges = {}
        if exchange_name and exchange_name in self.exchanges:
            target_exchanges[exchange_name] = self.exchanges[exchange_name]
        else:
            target_exchanges = self.exchanges

        if not target_exchanges:
            error_msg = f"No exchanges available. Requested: {exchange_name}"
            if self.logger:
                self.logger.error(error_msg)
            return {"error": error_msg}

        # Prepare order parameters
        order_params = {
            "symbol": symbol,
            "side": side,
            "amount": amount,
            "type": order_type,
        }

        # Add price for limit orders
        if order_type in ["limit", "stop_limit"] and price is not None:
            order_params["price"] = price

        # Add additional parameters
        order_params.update(kwargs)

        # Create orders on each exchange
        for ex_name, exchange in target_exchanges.items():
            try:
                if self.logger:
                    self.logger.info(
                        f"Creating {order_type} order on {ex_name}: {order_params}"
                    )

                # Create the order
                order = await exchange.create_order(**order_params)

                results[ex_name] = {
                    "success": True,
                    "order": order,
                    "order_id": order.get("id"),
                    "status": order.get("status"),
                    "filled": order.get("filled", 0),
                    "remaining": order.get("remaining", amount),
                }

                if self.logger:
                    self.logger.info(
                        f"Order created successfully on {ex_name}: {order.get('id')}"
                    )

            except Exception as e:
                error_msg = f"Failed to create order on {ex_name}: {str(e)}"
                results[ex_name] = {
                    "success": False,
                    "error": error_msg,
                    "exception_type": type(e).__name__,
                }

                if self.logger:
                    self.logger.error(error_msg)

        return results

    async def cancel_order(self, order_id: str, symbol: str, exchange_name: str = None):
        """
        Cancel an order on specified exchange or all exchanges.

        Args:
            order_id (str): Order ID to cancel
            symbol (str): Trading symbol
            exchange_name (str, optional): Specific exchange name. If None, tries all exchanges

        Returns:
            dict: Results from each exchange
        """
        results = {}

        # Determine which exchanges to use
        target_exchanges = {}
        if exchange_name and exchange_name in self.exchanges:
            target_exchanges[exchange_name] = self.exchanges[exchange_name]
        else:
            target_exchanges = self.exchanges

        for ex_name, exchange in target_exchanges.items():
            try:
                if self.logger:
                    self.logger.info(f"Cancelling order {order_id} on {ex_name}")

                cancel_result = await exchange.cancel_order(order_id, symbol)

                results[ex_name] = {
                    "success": True,
                    "cancelled": cancel_result,
                }

                if self.logger:
                    self.logger.info(
                        f"Order {order_id} cancelled successfully on {ex_name}"
                    )

            except Exception as e:
                error_msg = f"Failed to cancel order {order_id} on {ex_name}: {str(e)}"
                results[ex_name] = {
                    "success": False,
                    "error": error_msg,
                    "exception_type": type(e).__name__,
                }

                if self.logger:
                    self.logger.error(error_msg)

        return results

    async def get_open_orders(self, symbol: str = None, exchange_name: str = None):
        """
        Get open orders from specified exchange or all exchanges.

        Args:
            symbol (str, optional): Trading symbol to filter orders
            exchange_name (str, optional): Specific exchange name. If None, checks all exchanges

        Returns:
            dict: Open orders from each exchange
        """
        results = {}

        # Determine which exchanges to use
        target_exchanges = {}
        if exchange_name and exchange_name in self.exchanges:
            target_exchanges[exchange_name] = self.exchanges[exchange_name]
        else:
            target_exchanges = self.exchanges

        for ex_name, exchange in target_exchanges.items():
            try:
                if self.logger:
                    self.logger.info(f"Fetching open orders from {ex_name}")

                orders = (
                    await exchange.fetch_open_orders(symbol)
                    if symbol
                    else await exchange.fetch_open_orders()
                )

                results[ex_name] = {
                    "success": True,
                    "orders": orders,
                    "count": len(orders),
                }

                if self.logger:
                    self.logger.info(f"Found {len(orders)} open orders on {ex_name}")

            except Exception as e:
                error_msg = f"Failed to fetch open orders from {ex_name}: {str(e)}"
                results[ex_name] = {
                    "success": False,
                    "error": error_msg,
                    "exception_type": type(e).__name__,
                }

                if self.logger:
                    self.logger.error(error_msg)

        return results

    def fetch_market_data(self):
        """
        Fetches market data (price, volume, trades, NATR, spread, activity) for all exchanges.
        Returns:
            dict: {
                'mexc': {'btc': {...}, 'eth': {...}},
                'bingx': {...},
                'bitget': {...}
            }
        """
        # Example stub, replace with real websocket/API calls
        return {
            "mexc": {
                "btc": {
                    "delta": 0.5,
                    "vol": 0.5,
                    "trade": 300,
                    "NATR": 0.5,
                    "spred": 0.5,
                    "activity": 50,
                },
                "eth": {
                    "delta": 0.5,
                    "vol": 0.5,
                    "trade": 300,
                    "NATR": 0.5,
                    "spred": 0.5,
                    "activity": 50,
                },
            },
            "bingx": {
                "btc": {
                    "delta": 0.5,
                    "vol": 0.5,
                    "trade": 300,
                    "NATR": 0.5,
                    "spred": 0.5,
                    "activity": 50,
                },
                "eth": {
                    "delta": 0.5,
                    "vol": 0.5,
                    "trade": 300,
                    "NATR": 0.5,
                    "spred": 0.5,
                    "activity": 50,
                },
            },
            "bitget": {
                "btc": {
                    "delta": 0.5,
                    "vol": 0.5,
                    "trade": 300,
                    "NATR": 0.5,
                    "spred": 0.5,
                    "activity": 50,
                },
                "eth": {
                    "delta": 0.5,
                    "vol": 0.5,
                    "trade": 300,
                    "NATR": 0.5,
                    "spred": 0.5,
                    "activity": 50,
                },
            },
        }
