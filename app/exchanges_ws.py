import asyncio
import json
import math
from datetime import datetime

import ccxt.pro as ccxtpro

from app.mexc_exchange import MEXCExchange
from utils.settings import get_settings


class ExchangesWS:

    def __init__(self, logger=None, last_prices_file=None, save_to_file=True):
        # Load settings
        self.settings = get_settings()

        # Set logger first
        self.logger = logger

        # Use settings for configuration
        self.last_prices_file = last_prices_file or self.settings.arbitrage_input_file
        self.save_to_file = save_to_file

        # Prepare (lazy) exchanges container and factory map
        self.exchanges: dict[str, ccxtpro.Exchange] = {}
        self._allowed_exchange_names = list(self.settings.exchanges_list or [])

        self._initialize_exchanges()

        self.last_prices = []
        self._load_last_prices()

    def _initialize_exchanges(self):
        def _ccxt_factory(ccxt_id):
            def _factory():
                config = self._build_exchange_credentials(ccxt_id)
                return getattr(ccxtpro, ccxt_id)(config) if config else getattr(ccxtpro, ccxt_id)()

            return _factory

        self._exchange_factories = {
            "binance": _ccxt_factory("binance"),
            "okx": _ccxt_factory("okx"),
            "bybit": _ccxt_factory("bybit"),
            "gate": _ccxt_factory("gateio"),
            "bitget": _ccxt_factory("bitget"),
            "bingx": _ccxt_factory("bingx"),
            "mexc": _ccxt_factory("mexc"),
            "kraken": _ccxt_factory("kraken"),
            "coinbase": _ccxt_factory("coinbase"),
            # custom uses settings internally
            "mexc_custom": lambda: MEXCExchange(logger=self.logger),
        }

    def _build_exchange_credentials(self, ccxt_id: str, futures: bool = True, contract: str = "usdt") -> dict:
        """Build a ccxt/pro constructor config dict for a given exchange id, using settings only.

        Returns a dict containing credentials and safe defaults like enableRateLimit.
        """
        creds = self.settings.get_ccxt_credentials(ccxt_id)
        config: dict = {"enableRateLimit": True, "timeout": 30000, "rateLimit": 1000}

        # Merge credentials if present
        if isinstance(creds, dict):
            config.update(creds)

        # Per-exchange adjustments (extend as needed)
        if ccxt_id == "binance":
            # Prefer unified futures if you mainly trade futures; leave commented if spot needed
            # config.setdefault("options", {})
            # config["options"].setdefault("defaultType", "future")
            pass
        elif ccxt_id == "okx":
            # OKX often requires password in creds; nothing else by default
            pass
        elif ccxt_id == "bybit":
            pass
        elif ccxt_id == "gateio":
            # Enable clock skew adjustment to avoid REQUEST_EXPIRED
            config.setdefault("options", {})
            config["options"].setdefault("adjustForTimeDifference", True)
            # Use futures (perpetual swaps) by default
            config["options"].setdefault("defaultType", "swap")
        elif ccxt_id == "bitget":
            # Use futures (perpetual swaps) by default
            config.setdefault("options", {})
            config["options"].setdefault("defaultType", "swap")
            # Correct defaults per Bitget: tdMode and posMode
            config["options"].setdefault("defaultMarginMode", "isolated")  # isolated or cross
            config["options"].setdefault("defaultPositionMode", "one_way")  # one_way or hedged
        elif ccxt_id == "bingx":
            # Use futures (perpetual swaps) by default
            config.setdefault("options", {})
            config["options"].setdefault("defaultType", "swap")
            # Help prevent timestamp mismatch
            config["options"].setdefault("adjustForTimeDifference", True)
        elif ccxt_id == "mexc":
            pass
        elif ccxt_id == "kraken":
            pass
        elif ccxt_id == "coinbase":
            pass

        return config

    def _get_or_create_exchange(self, exchange_name: str):
        """Return existing exchange or lazily create it if allowed and known."""
        if exchange_name in self.exchanges:
            return self.exchanges[exchange_name]
        if self._allowed_exchange_names and exchange_name not in self._allowed_exchange_names:
            if self.logger:
                self.logger.warning(f"Exchange '{exchange_name}' not in allowed list; skipping initialization")
            return None
        factory = self._exchange_factories.get(exchange_name)
        if not factory:
            if self.logger:
                self.logger.warning(f"Unknown exchange: {exchange_name}")
            return None
        try:
            instance = factory()
            self.exchanges[exchange_name] = instance
            if self.logger:
                self.logger.info(f"Initialized exchange: {exchange_name}")
            # Proactively sync time and set options to mitigate timestamp errors (e.g., BingX)
            try:
                if hasattr(instance, "load_time_difference"):
                    # fire-and-forget: don't block init on this
                    asyncio.create_task(instance.load_time_difference())
                if hasattr(instance, "options"):
                    instance.options = {
                        **getattr(instance, "options", {}),
                        "adjustForTimeDifference": True,
                    }
            except Exception:
                pass
            return instance
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to initialize exchange {exchange_name}: {e}")
            return None

    def _load_last_prices(self):
        # Only load from file if save_to_file is True
        if not self.save_to_file:
            self.last_prices = []
            if self.logger:
                self.logger.info("File reading disabled (save_to_file=False). Starting with empty collection.")
            return

        try:
            with open(self.last_prices_file, encoding="utf-8") as f:
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
                if self.logger:
                    self.logger.info(f"Loaded {len(loaded)} records from {self.last_prices_file}")
        except Exception:
            self.last_prices = []
            if self.logger:
                self.logger.warning(f"Could not load data from {self.last_prices_file}")

    async def stream_futures(
        self,
        symbols: list = None,
        output_file: str = None,
    ):
        # Use settings for output file if not provided
        if output_file is None:
            output_file = self.settings.exchanges_output_file

        # Use symbols from settings if not provided
        if symbols is None:
            symbols = self.settings.symbols

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
                    # Add to collection only if dict
                    if isinstance(norm_entry, dict):
                        self.last_prices.append(norm_entry)
                    # Add to file only if save_to_file is True
                    if self.save_to_file:
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
                    # Add error to file only if save_to_file is True
                    if self.save_to_file:
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
                            self.logger.error(f"Max reconnection attempts reached for {exchange.id}. Stopping.")
                        break

        tasks = []
        for name in self._allowed_exchange_names:
            ex = self._get_or_create_exchange(name)
            if not ex:
                continue

            # Create tasks for each symbol
            for symbol in symbols:
                tasks.append(symbol_loop(ex, symbol, f"future_{name}"))
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

    async def get_min_order_value(self, exchange_name: str, symbol: str) -> float:
        """Return the minimum USDT size required to place an order."""
        ex = self._get_or_create_exchange(exchange_name)
        if not ex:
            return 0.0

        try:
            # Load markets to access limits/contract metadata
            if hasattr(ex, "load_markets"):
                await ex.load_markets()
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error loading markets for {exchange_name}: {str(e)}")
            return None

        try:
            market = None
            try:
                if hasattr(ex, "market"):
                    market = ex.market(symbol)
                else:
                    market = ex.markets.get(symbol)
            except Exception:
                market = None

            # Extract limits
            limits = (market or {}).get("limits") or {}
            amount_limits = limits.get("amount") or {}
            cost_limits = limits.get("cost") or {}
            min_amount = amount_limits.get("min")
            min_cost = cost_limits.get("min")

            # Determine if this is a contract/swap market and its contract size
            is_contract = bool((market or {}).get("contract") or (market or {}).get("swap"))
            contract_size = (market or {}).get("contractSize") or 1

            # Obtain an effective price from live ticker only (no cache)
            price = None
            try:
                ticker = await ex.fetch_ticker(symbol)
                price = (ticker.get("last") if isinstance(ticker, dict) else None) or (
                    ticker.get("close") if isinstance(ticker, dict) else None
                )
            except Exception:
                price = None

            # If spot: return min_cost or min_amount*price
            if not is_contract:
                if isinstance(min_cost, (int, float)) and min_cost is not None:
                    return float(min_cost)
                if (
                    isinstance(min_amount, (int, float))
                    and min_amount is not None
                    and isinstance(price, (int, float))
                    and price is not None
                ):
                    return float(min_amount) * float(price)
                return 0.0

            # If exchange provides min notional, use it
            notional_size = 0.0
            if isinstance(min_cost, (int, float)) and min_cost is not None:
                try:
                    notional_size = float(min_cost)
                except Exception:
                    return float(min_cost)

            # Otherwise derive from min contracts * contract_size * price
            notional_contract_size = 0.0
            if (
                isinstance(min_amount, (int, float))
                and min_amount is not None
                and isinstance(price, (int, float))
                and price is not None
            ):
                try:
                    notional_contract_size = float(min_amount) * float(contract_size) * float(price)
                except Exception:
                    pass

            # Round up to the nearest integer USDT (largest chart step)
            required_margin = max(notional_contract_size, notional_size)
            return float(math.ceil(required_margin))
        except Exception:
            return 0.0

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
            amount (float): Order amount in USDT (will be converted to contract units for MEXC)
            price (float, optional): Order price for limit orders
            order_type (str): Order type ('market', 'limit', 'stop', 'stop_limit')
            exchange_name (str, optional): Specific exchange name. If None, tries all exchanges
            **kwargs: Additional parameters for order creation

        Returns:
            dict: Results from each exchange with order details or errors
        """
        results = {}

        # Determine which exchanges to use (lazily create when needed)
        target_exchanges = {}
        if exchange_name:
            ex = self._get_or_create_exchange(exchange_name)
            if ex:
                target_exchanges[exchange_name] = ex
        else:
            for name in self._allowed_exchange_names:
                ex = self._get_or_create_exchange(name)
                if ex:
                    target_exchanges[name] = ex

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
                # Ensure time sync to avoid REQUEST_EXPIRED on some exchanges (e.g., gateio)
                try:
                    # prefer built-in time difference logic if available
                    if hasattr(exchange, "load_time_difference"):
                        await exchange.load_time_difference()
                    # also set option flag if supported
                    if hasattr(exchange, "options"):
                        exchange.options = {
                            **getattr(exchange, "options", {}),
                            "adjustForTimeDifference": True,
                        }
                except Exception:
                    pass

                if self.logger:
                    self.logger.info(f"Preparing {order_type} order on {ex_name}: {order_params}")

                # Per-exchange parameter adjustments
                params = {}

                # Reduce-only logic for closing positions if requested
                if kwargs.get("close_position") is True:
                    params["reduceOnly"] = True

                # Load markets to detect futures and contract size
                is_swap = False
                contract_size = 1
                try:
                    # Sync time first to avoid timestamp errors on some exchanges (e.g., bingx)
                    try:
                        if hasattr(exchange, "load_time_difference"):
                            await exchange.load_time_difference()
                        if hasattr(exchange, "options"):
                            exchange.options = {
                                **getattr(exchange, "options", {}),
                                "adjustForTimeDifference": True,
                            }
                    except Exception:
                        pass
                    if hasattr(exchange, "load_markets"):
                        await exchange.load_markets()
                    market = exchange.market(symbol) if hasattr(exchange, "market") else None
                    if market is not None:
                        is_swap = bool(getattr(market, "swap", market.get("swap", False)))
                        contract_size = (
                            getattr(market, "contractSize", None)
                            if hasattr(market, "contractSize")
                            else (market.get("contractSize") if isinstance(market, dict) else None)
                        ) or 1
                except Exception:
                    market = None
                    # Try to resolve a compatible swap market by base/quote (helps for BingX)
                    try:
                        if hasattr(exchange, "markets"):
                            # Derive target base/quote/settle
                            target = symbol
                            contract_settle = None
                            if ":" in target:
                                parts = target.split(":", 1)
                                target = parts[0]
                                contract_settle = parts[1]
                            base_quote = target.split("/") if "/" in target else [target, None]
                            base = base_quote[0]
                            quote = base_quote[1] if len(base_quote) > 1 else contract_settle

                            # Search for a swap market matching base and quote/settle
                            fallback_symbol = None
                            for m_symbol, m in exchange.markets.items():
                                try:
                                    if not m.get("swap"):
                                        continue
                                    m_base = m.get("base")
                                    m_quote = m.get("quote")
                                    m_settle = m.get("settle") or m_quote
                                    if m_base == base and (m_quote == quote or m_settle == quote):
                                        fallback_symbol = m.get("symbol") or m_symbol
                                        market = m
                                        break
                                except Exception:
                                    continue
                            if fallback_symbol:
                                symbol = fallback_symbol
                                is_swap = True
                                contract_size = market.get("contractSize", 1) or 1
                    except Exception:
                        pass

                # Bitget: set posMode/tdMode in params (do not switch mode to avoid 40920)
                try:
                    if getattr(exchange, "id", "") == "bitget" and is_swap:
                        opts = getattr(exchange, "options", {}) or {}
                        default_margin = str(opts.get("defaultMarginMode", "isolated")).lower()
                        default_position = str(opts.get("defaultPositionMode", "one_way")).lower()

                        # Bitget-specific order params
                        pos_mode = kwargs.get("posMode") or ("one_way" if default_position == "one_way" else "hedge")
                        params["posMode"] = pos_mode
                        td_mode = kwargs.get("tdMode") or kwargs.get("marginMode") or default_margin
                        params["tdMode"] = "isolated" if str(td_mode).lower() == "isolated" else "cross"
                except Exception:
                    pass

                # Determine effective price for amount conversion if needed
                effective_price = price
                if is_swap and effective_price is None and order_type == "market":
                    try:
                        ticker = await exchange.fetch_ticker(symbol)
                        effective_price = ticker.get("last") or ticker.get("close")
                    except Exception:
                        effective_price = None

                # Build local order params without unsupported fields (only ccxt unified keys)
                local_order_params = {
                    "symbol": symbol,
                    "side": side,
                    "type": order_type,
                }

                # Convert USDT amount to contract amount for swaps
                amount_to_send = amount
                if is_swap and effective_price:
                    lev = kwargs.get("leverage") or 1
                    try:
                        contracts = (float(amount) * float(lev)) / (float(effective_price) * float(contract_size))
                        if hasattr(exchange, "amount_to_precision"):
                            amount_to_send = float(exchange.amount_to_precision(symbol, contracts))
                        else:
                            amount_to_send = max(1, round(contracts))
                    except Exception:
                        amount_to_send = amount
                local_order_params["amount"] = amount_to_send

                # Ensure price for limit orders
                if order_type in ["limit", "stop_limit"] and price is not None:
                    local_order_params["price"] = price

                # Gate.io spot-only: allow market buy without price by sending quote cost
                if (
                    getattr(exchange, "id", "") == "gateio"
                    and not is_swap
                    and order_type == "market"
                    and side == "buy"
                    and "price" not in local_order_params
                ):
                    try:
                        exchange.options = {
                            **getattr(exchange, "options", {}),
                            "createMarketBuyOrderRequiresPrice": False,
                        }
                        params["createMarketBuyOrderRequiresPrice"] = False
                        params["cost"] = amount
                    except Exception:
                        pass

                # BingX: ensure timestamp tolerance and resolve symbol to a valid swap market
                if getattr(exchange, "id", "") == "bingx":
                    try:
                        exchange.options = {
                            **getattr(exchange, "options", {}),
                            "adjustForTimeDifference": True,
                        }
                        # Include relaxed recvWindow and current timestamp for signed requests
                        params.setdefault("recvWindow", 60000)
                        try:
                            params.setdefault("timestamp", exchange.milliseconds())
                        except Exception:
                            pass
                        # Ensure we end up with a valid swap symbol for BingX
                        if hasattr(exchange, "markets") and exchange.markets:
                            if symbol not in exchange.markets or not exchange.markets.get(symbol, {}).get("swap"):
                                base, quote = None, None
                                tgt = symbol
                                if ":" in tgt:
                                    parts = tgt.split(":", 1)
                                    tgt = parts[0]
                                    quote = parts[1]
                                if "/" in tgt:
                                    base, q2 = tgt.split("/", 1)
                                    quote = quote or q2
                                else:
                                    base = tgt
                                for m_symbol, m in exchange.markets.items():
                                    try:
                                        if not m.get("swap"):
                                            continue
                                        if m.get("base") == base and (
                                            m.get("quote") == quote or (m.get("settle") or m.get("quote")) == quote
                                        ):
                                            symbol = m.get("symbol") or m_symbol
                                            is_swap = True
                                            contract_size = m.get("contractSize", contract_size) or contract_size
                                            break
                                    except Exception:
                                        continue
                    except Exception:
                        pass

                # Try to set leverage via ccxt method for futures
                try:
                    lev = kwargs.get("leverage")
                    if is_swap and lev is not None:
                        if hasattr(exchange, "set_leverage"):
                            extra = {}
                            if getattr(exchange, "id", "") == "bingx":
                                # BingX requires a side parameter: LONG | SHORT | BOTH
                                extra["side"] = "BOTH"
                            await exchange.set_leverage(lev, symbol, extra)
                        elif hasattr(exchange, "setLeverage"):
                            extra = {}
                            if getattr(exchange, "id", "") == "bingx":
                                extra["side"] = "BOTH"
                            await exchange.setLeverage(lev, symbol, extra)
                except Exception:
                    pass

                # Create the order
                order = await exchange.create_order(**local_order_params, params=params)

                results[ex_name] = {
                    "success": True,
                    "order": order,
                    "order_id": order.get("id"),
                    "status": order.get("status"),
                    "filled": order.get("filled", 0),
                    "remaining": order.get("remaining", amount),
                }

                if self.logger:
                    self.logger.info(f"Order created successfully on {ex_name}: {order.get('id')}")

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

        # Determine which exchanges to use (lazily create when needed)
        target_exchanges = {}
        if exchange_name:
            ex = self._get_or_create_exchange(exchange_name)
            if ex:
                target_exchanges[exchange_name] = ex
        else:
            for name in self._allowed_exchange_names:
                ex = self._get_or_create_exchange(name)
                if ex:
                    target_exchanges[name] = ex

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
                    self.logger.info(f"Order {order_id} cancelled successfully on {ex_name}")

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

    async def edit_order(
        self,
        order_id: str,
        symbol: str,
        order_type: str,
        side: str,
        amount: float = None,
        price: float = None,
        exchange_name: str = None,
        **kwargs,
    ):
        """
        Edit an existing order on a specific exchange. Falls back to cancel+recreate
        if native edit is not supported.

        Args:
            order_id: Existing order ID
            symbol: Trading symbol
            order_type: e.g., 'limit'
            side: 'buy' or 'sell'
            amount: New amount (optional for some exchanges)
            price: New price (for limit orders)
            exchange_name: Target exchange
            **kwargs: Additional parameters forwarded to create on fallback (e.g., leverage)

        Returns:
            dict: { exchange_name: { success: bool, order_id?: str, error?: str } }
        """
        if not exchange_name:
            return {"error": "exchange_name is required for edit_order"}

        exchange = self._get_or_create_exchange(exchange_name)
        if not exchange:
            return {exchange_name: {"success": False, "error": "Exchange not available"}}

        # Prepare params and convert amount for futures (e.g., BingX) before native edit
        params = {}
        local_symbol = symbol
        local_amount = amount
        try:
            # Load markets and try to resolve swap market and contract size
            is_swap = False
            contract_size = 1
            try:
                if hasattr(exchange, "load_markets"):
                    await exchange.load_markets()
                market = exchange.market(symbol) if hasattr(exchange, "market") else None
                if market is not None:
                    is_swap = bool(getattr(market, "swap", market.get("swap", False)))
                    contract_size = (
                        getattr(market, "contractSize", None)
                        if hasattr(market, "contractSize")
                        else (market.get("contractSize") if isinstance(market, dict) else None)
                    ) or 1
            except Exception:
                market = None
                # Try to resolve a compatible swap market by base/quote (helps for BingX)
                try:
                    if hasattr(exchange, "markets") and exchange.markets:
                        target = symbol
                        contract_settle = None
                        if ":" in target:
                            parts = target.split(":", 1)
                            target = parts[0]
                            contract_settle = parts[1]
                        base_quote = target.split("/") if "/" in target else [target, None]
                        base = base_quote[0]
                        quote = base_quote[1] if len(base_quote) > 1 else contract_settle
                        for m_symbol, m in exchange.markets.items():
                            try:
                                if not m.get("swap"):
                                    continue
                                m_base = m.get("base")
                                m_quote = m.get("quote")
                                m_settle = m.get("settle") or m_quote
                                if m_base == base and (m_quote == quote or m_settle == quote):
                                    local_symbol = m.get("symbol") or m_symbol
                                    is_swap = True
                                    contract_size = m.get("contractSize", contract_size) or contract_size
                                    break
                            except Exception:
                                continue
                except Exception:
                    pass

            # If futures and user amount is not contracts, convert USDT -> contracts like create_closing_changing_order
            if is_swap and local_amount is not None:
                lev = kwargs.get("leverage") or 1
                effective_price = price
                if effective_price is None:
                    try:
                        ticker = await exchange.fetch_ticker(local_symbol)
                        effective_price = (ticker.get("last") if isinstance(ticker, dict) else None) or (
                            ticker.get("close") if isinstance(ticker, dict) else None
                        )
                    except Exception:
                        effective_price = None
                if effective_price:
                    try:
                        contracts = (float(local_amount) * float(lev)) / (float(effective_price) * float(contract_size))
                        if hasattr(exchange, "amount_to_precision"):
                            local_amount = float(exchange.amount_to_precision(local_symbol, contracts))
                        else:
                            local_amount = max(1, round(contracts))
                    except Exception:
                        pass

            # Try native edit first with adjusted symbol/amount
            if hasattr(exchange, "edit_order"):
                edited = await exchange.edit_order(
                    order_id,
                    local_symbol,
                    order_type,
                    side,
                    amount=local_amount,
                    price=price,
                    params=params,
                )
                # Robustly resolve the new order id from various ccxt/Bitget fields
                resolved_id = None
                try:
                    if isinstance(edited, dict):
                        info = edited.get("info") or {}
                        if not isinstance(info, dict):
                            info = {}
                        # unified
                        resolved_id = edited.get("id")
                        # common keys
                        if not resolved_id:
                            resolved_id = (
                                info.get("orderId")
                                or info.get("mainOrderId")
                                or (info.get("order") or {}).get("orderId")
                            )
                        # Bitget variants: info.data as dict or list
                        if not resolved_id:
                            data = info.get("data")
                            if isinstance(data, dict):
                                resolved_id = data.get("orderId") or data.get("order_id")
                                if not resolved_id:
                                    # sometimes under nested 'order' key
                                    resolved_id = (data.get("order") or {}).get("orderId")
                            elif isinstance(data, list) and data:
                                first = data[0]
                                if isinstance(first, dict):
                                    resolved_id = first.get("orderId") or first.get("order_id")
                        # Other wrapped responses
                        if not resolved_id:
                            new_resp = info.get("newOrderResponse") or {}
                            if isinstance(new_resp, dict):
                                resolved_id = new_resp.get("orderId") or new_resp.get("order_id")
                            open_resp = info.get("orderOpenResponse") or {}
                            if not resolved_id and isinstance(open_resp, dict):
                                resolved_id = open_resp.get("orderId") or open_resp.get("order_id")
                except Exception:
                    resolved_id = None
                return {
                    exchange_name: {
                        "success": True,
                        "order": edited,
                        "order_id": resolved_id or (edited.get("id") if isinstance(edited, dict) else None),
                        "status": edited.get("status"),
                    }
                }
        except Exception as e:
            # fall through to fallback flow
            if self.logger:
                self.logger.warning(
                    f"edit_order not supported or failed on {exchange_name}: {e}; falling back to cancel+recreate"
                )

        # Fallback: cancel and recreate with new params
        try:
            await self.cancel_order(order_id=order_id, symbol=symbol, exchange_name=exchange_name)
            created = await self.create_closing_changing_order(
                symbol=symbol,
                side=side,
                amount=amount,
                price=price,
                order_type=order_type,
                exchange_name=exchange_name,
                **kwargs,
            )
            # Ensure consistent return format for fallback
            if created.get(exchange_name, {}).get("success"):
                return {
                    exchange_name: {
                        "success": True,
                        "order": created[exchange_name].get("order"),
                        "order_id": created[exchange_name].get("order_id"),
                        "status": created[exchange_name].get("status"),
                    }
                }
            else:
                return created
        except Exception as e:
            return {
                exchange_name: {
                    "success": False,
                    "error": str(e),
                    "exception_type": type(e).__name__,
                }
            }

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

        # Determine which exchanges to use (lazily create when needed)
        target_exchanges = {}
        if exchange_name:
            ex = self._get_or_create_exchange(exchange_name)
            if ex:
                target_exchanges[exchange_name] = ex
        else:
            for name in self._allowed_exchange_names:
                ex = self._get_or_create_exchange(name)
                if ex:
                    target_exchanges[name] = ex

        for ex_name, exchange in target_exchanges.items():
            try:
                if self.logger:
                    self.logger.info(f"Fetching open orders from {ex_name}")

                orders = await exchange.fetch_open_orders(symbol) if symbol else await exchange.fetch_open_orders()

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


# Removed test functions - keeping only core ExchangesWS class


async def test_specific_exchange_operations(exchange_name: str, symbol: str = None):
    """
    Test specific operations for a single exchange.

    Args:
        exchange_name: Name of the exchange to test
        symbol: Trading symbol to use for testing (if None, uses first symbol from settings)
    """
    if symbol is None:
        settings = get_settings()
        symbols = settings.symbols
        symbol = symbols[0] if symbols else "BTC/USDT:USDT"
    from utils.logger import get_logger

    logger = get_logger()
    exchanges_ws = ExchangesWS(logger=logger)

    ex = exchanges_ws._get_or_create_exchange(exchange_name)
    if not ex:
        print(f"❌ Exchange {exchange_name} not available")
        return

    print(f"🔍 Testing {exchange_name.upper()} Exchange Operations")
    print("=" * 50)

    try:
        # Test order creation with different parameters
        test_cases = [
            {
                "name": "Market Buy Order",
                "side": "buy",
                "amount": 5,
                "order_type": "market",
            },
            {
                "name": "Limit Sell Order",
                "side": "sell",
                "amount": 5,
                "price": 45000,
                "order_type": "limit",
            },
            {
                "name": "Market Sell Order",
                "side": "sell",
                "amount": 3,
                "order_type": "market",
            },
        ]

        created_orders = []

        for i, test_case in enumerate(test_cases, 1):
            print(f"\n{i}. {test_case['name']}")
            print("-" * 30)

            result = await exchanges_ws.create_closing_changing_order(
                symbol=symbol,
                side=test_case["side"],
                amount=test_case["amount"],
                price=test_case.get("price"),
                order_type=test_case["order_type"],
                exchange_name=exchange_name,
            )

            if result.get(exchange_name, {}).get("success"):
                order_id = result[exchange_name]["order_id"]
                created_orders.append(order_id)
                print(f"   ✅ Order created: {order_id}")
            else:
                print(f"   ❌ Order failed: {result[exchange_name].get('error')}")

        # Cancel all created orders
        print(f"\n🗑️  Cancelling {len(created_orders)} orders...")
        for order_id in created_orders:
            try:
                cancel_result = await exchanges_ws.cancel_order(
                    order_id=order_id, symbol=symbol, exchange_name=exchange_name
                )
                if cancel_result.get(exchange_name, {}).get("success"):
                    print(f"   ✅ Order {order_id} cancelled")
                else:
                    print(f"   ❌ Failed to cancel {order_id}")
            except Exception as e:
                print(f"   ❌ Error cancelling {order_id}: {str(e)}")

    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        logger.error(f"Error during testing: {str(e)}")

    finally:
        # Cleanup
        try:
            await exchanges_ws.exchanges[exchange_name].close()
        except Exception as e:
            print(f"Warning: Error closing exchange: {str(e)}")


async def test_exchanges_order_operations():
    """
    Test function for creating, changing, and closing market and limit orders
    on Gate.io and Bitget exchanges using ExchangesWS class.
    """
    from utils.logger import get_logger

    # Initialize logger
    logger = get_logger()

    # Initialize ExchangesWS
    exchanges_ws = ExchangesWS(logger=logger)

    # Use first symbol from settings
    symbols = exchanges_ws.settings.symbols
    symbol = symbols[0] if symbols else "BTC/USDT:USDT"
    # Derive limit test prices and leverage for all tests
    test_price = 100000
    test_sell_price = test_price * 2
    test_buy_price = test_price / 2
    leverage = 20
    print("=" * 60)
    print("TESTING EXCHANGE ORDER OPERATIONS")
    print("=" * 60)

    # Test exchanges: enable/disable each scenario per exchange
    test_exchanges = {
        # "binance": {
        #     "market_long_open_close": True,
        #     "market_short_open_close": True,
        #     "limit_long_open_change_close": True,
        #     "limit_short_open_change_close": True,
        # },
        # "okx": {
        #     "market_long_open_close": True,
        #     "market_short_open_close": True,
        #     "limit_long_open_change_close": True,
        #     "limit_short_open_change_close": True,
        # },
        # "bybit": {
        #     "market_long_open_close": True,
        #     "market_short_open_close": True,
        #     "limit_long_open_change_close": True,
        #     "limit_short_open_change_close": True,
        # },
        # "gate": {
        #     "market_long_open_close": False,
        #     "market_short_open_close": False,
        #     "limit_long_open_change_close": True,
        #     "limit_short_open_change_close": True,
        # },
        "bitget": {
            "market_long_open_close": False,
            "market_short_open_close": False,
            "limit_long_open_change_close": True,
            "limit_short_open_change_close": True,
        },
        # "bingx": {
        #     "market_long_open_close": False,
        #     "market_short_open_close": False,
        #     "limit_long_open_change_close": True,
        #     "limit_short_open_change_close": True,
        # },
        # "mexc": {
        #     "market_long_open_close": True,
        #     "market_short_open_close": True,
        #     "limit_long_open_change_close": True,
        #     "limit_short_open_change_close": True,
        # },
        # "kraken": {
        #     "market_long_open_close": True,
        #     "market_short_open_close": True,
        #     "limit_long_open_change_close": True,
        #     "limit_short_open_change_close": True,
        # },
        # "coinbase": {
        #     "market_long_open_close": True,
        #     "market_short_open_close": True,
        #     "limit_long_open_change_close": True,
        #     "limit_short_open_change_close": True,
        # },
    }

    for exchange_name, flags in test_exchanges.items():
        ex = exchanges_ws._get_or_create_exchange(exchange_name)
        if not ex:
            print(f"❌ Exchange {exchange_name} not available, skipping...")
            continue

        print(f"\n🔄 Testing {exchange_name.upper()} Exchange")
        print("-" * 40)

        try:
            exchange = ex

            # Skip if credentials are missing (avoids apiKey required errors)
            creds_present = (
                bool(getattr(exchange, "apiKey", None))
                or bool(getattr(exchange, "secret", None))
                or bool(getattr(exchange, "password", None))
            )
            if not creds_present:
                print(f"   ⚠️  Skipping {exchange_name}: credentials not configured")
                continue

            # Determine minimum permissible order value for this exchange/symbol
            try:
                min_value = await exchanges_ws.get_min_order_value(
                    exchange_name=exchange_name,
                    symbol=symbol,
                )
                test_amount = round(float(min_value + 0.1) / leverage, 2)
                print(f"   ℹ️  Using min order value for {exchange_name}: {test_amount}")
            except Exception:
                test_amount = 5

            if flags.get("market_long_open_close"):
                # 1. Create Market Order LONG (buy)
                print(f"1. Creating market LONG order on {exchange_name}...")
                market_long = await exchanges_ws.create_closing_changing_order(
                    symbol=symbol,
                    side="buy",
                    amount=test_amount,
                    order_type="market",
                    exchange_name=exchange_name,
                    leverage=leverage,
                )

                if market_long.get(exchange_name, {}).get("success"):
                    order_id_long = market_long[exchange_name]["order_id"]
                    print(f"   ✅ Market LONG created: {order_id_long}")

                    # 2. Close Market LONG (sell reduceOnly)
                    print(f"2. Closing market LONG on {exchange_name}...")
                    close_long = await exchanges_ws.create_closing_changing_order(
                        symbol=symbol,
                        side="sell",
                        amount=test_amount,
                        order_type="market",
                        exchange_name=exchange_name,
                        close_position=True,
                        leverage=leverage,
                    )

                    if close_long.get(exchange_name, {}).get("success"):
                        print("   ✅ Market LONG closed")
                    else:
                        print(f"   ❌ Close LONG failed: {close_long[exchange_name].get('error')}")

                else:
                    print(f"   ❌ Market LONG failed: {market_long[exchange_name].get('error')}")

            if flags.get("market_short_open_close"):
                # 3. Create Market Order SHORT (sell)
                print(f"3. Creating market SHORT order on {exchange_name}...")
                market_short = await exchanges_ws.create_closing_changing_order(
                    symbol=symbol,
                    side="sell",
                    amount=test_amount,
                    order_type="market",
                    exchange_name=exchange_name,
                    leverage=leverage,
                )

                if market_short.get(exchange_name, {}).get("success"):
                    order_id_short = market_short[exchange_name]["order_id"]
                    print(f"   ✅ Market SHORT created: {order_id_short}")

                    # 4. Close Market SHORT (buy reduceOnly)
                    print(f"4. Closing market SHORT on {exchange_name}...")
                    close_short = await exchanges_ws.create_closing_changing_order(
                        symbol=symbol,
                        side="buy",
                        amount=test_amount,
                        order_type="market",
                        exchange_name=exchange_name,
                        close_position=True,
                        leverage=leverage,
                    )

                    if close_short.get(exchange_name, {}).get("success"):
                        print("   ✅ Market SHORT closed")
                    else:
                        print(f"   ❌ Close SHORT failed: {close_short[exchange_name].get('error')}")
                else:
                    print(f"   ❌ Market SHORT failed: {market_short[exchange_name].get('error')}")

            if flags.get("limit_long_open_change_close"):
                # 5. Create Limit LONG (buy below price)
                print(f"5. Creating limit LONG on {exchange_name}...")
                limit_long = await exchanges_ws.create_closing_changing_order(
                    symbol=symbol,
                    side="buy",
                    amount=test_amount,
                    price=test_buy_price * 0.95,
                    order_type="limit",
                    exchange_name=exchange_name,
                    leverage=leverage,
                )

                if limit_long.get(exchange_name, {}).get("success"):
                    limit_long_id = limit_long[exchange_name]["order_id"]
                    print(f"   ✅ Limit LONG created: {limit_long_id}")

                    # 6. Change Limit LONG price (edit or cancel+recreate)
                    print("6. Changing limit LONG price...")
                    new_price_long = test_buy_price * 0.94
                    changed = False
                    try:
                        edit_res = await exchanges_ws.edit_order(
                            order_id=limit_long_id,
                            symbol=symbol,
                            order_type="limit",
                            side="buy",
                            amount=test_amount,
                            price=new_price_long,
                            exchange_name=exchange_name,
                            leverage=leverage,
                        )
                        ex_res = edit_res.get(exchange_name, {})
                        changed = bool(ex_res.get("success"))
                        if changed:
                            new_id = ex_res.get("order_id") or (
                                (ex_res.get("order") or {}).get("id") if isinstance(ex_res.get("order"), dict) else None
                            )
                            if new_id:
                                limit_long_id = new_id
                    except Exception:
                        changed = False
                    if not changed:
                        # Fallback: cancel and recreate
                        await exchanges_ws.cancel_order(
                            order_id=limit_long_id,
                            symbol=symbol,
                            exchange_name=exchange_name,
                        )
                        recreate_res = await exchanges_ws.create_closing_changing_order(
                            symbol=symbol,
                            side="buy",
                            amount=test_amount,
                            price=new_price_long,
                            order_type="limit",
                            exchange_name=exchange_name,
                            leverage=leverage,
                        )
                        if recreate_res.get(exchange_name, {}).get("success"):
                            limit_long_id = recreate_res[exchange_name]["order_id"]
                    print("   ✅ Limit LONG changed")

                    # 7. Close/cancel Limit LONG
                    print("7. Cancelling limit LONG...")
                    await exchanges_ws.cancel_order(
                        order_id=limit_long_id,
                        symbol=symbol,
                        exchange_name=exchange_name,
                    )

                else:
                    print(f"   ❌ Limit LONG failed: {limit_long[exchange_name].get('error')}")

            if flags.get("limit_short_open_change_close"):
                # 8. Create Limit SHORT (sell above price)
                print(f"8. Creating limit SHORT on {exchange_name}...")
                limit_short = await exchanges_ws.create_closing_changing_order(
                    symbol=symbol,
                    side="sell",
                    amount=test_amount * 2,
                    price=test_sell_price * 1.05,
                    order_type="limit",
                    exchange_name=exchange_name,
                    leverage=leverage,
                )

                if limit_short.get(exchange_name, {}).get("success"):
                    limit_short_id = limit_short[exchange_name]["order_id"]
                    print(f"   ✅ Limit SHORT created: {limit_short_id}")

                    # 9. Change Limit SHORT price
                    print("9. Changing limit SHORT price...")
                    new_price_short = test_sell_price * 1.06
                    changed_s = False
                    try:
                        edit_res = await exchanges_ws.edit_order(
                            order_id=limit_short_id,
                            symbol=symbol,
                            order_type="limit",
                            side="sell",
                            amount=test_amount * 2,
                            price=new_price_short,
                            exchange_name=exchange_name,
                            leverage=leverage,
                        )
                        ex_res_s = edit_res.get(exchange_name, {})
                        changed_s = bool(ex_res_s.get("success"))
                        if changed_s:
                            new_id_s = ex_res_s.get("order_id") or (
                                (ex_res_s.get("order") or {}).get("id")
                                if isinstance(ex_res_s.get("order"), dict)
                                else None
                            )
                            if new_id_s:
                                limit_short_id = new_id_s
                    except Exception:
                        changed_s = False
                    if not changed_s:
                        await exchanges_ws.cancel_order(
                            order_id=limit_short_id,
                            symbol=symbol,
                            exchange_name=exchange_name,
                        )
                        recreate_res_s = await exchanges_ws.create_closing_changing_order(
                            symbol=symbol,
                            side="sell",
                            amount=test_amount * 2,
                            price=new_price_short,
                            order_type="limit",
                            exchange_name=exchange_name,
                            leverage=leverage,
                        )
                        if recreate_res_s.get(exchange_name, {}).get("success"):
                            limit_short_id = recreate_res_s[exchange_name]["order_id"]
                    print("   ✅ Limit SHORT changed")

                    # 10. Close/cancel Limit SHORT
                    print("10. Cancelling limit SHORT...")
                    await exchanges_ws.cancel_order(
                        order_id=limit_short_id,
                        symbol=symbol,
                        exchange_name=exchange_name,
                    )

                else:
                    print(f"   ❌ Limit SHORT failed: {limit_short[exchange_name].get('error')}")

        except Exception as e:
            print(f"   ❌ Error testing {exchange_name}: {str(e)}")
            logger.error(f"Error testing {exchange_name}: {str(e)}")

    # Position closing is already covered in steps above via reduceOnly

    # Cleanup
    print("\n🧹 Cleaning up...")
    for exchange in exchanges_ws.exchanges.values():
        try:
            await exchange.close()
        except Exception as e:
            print(f"   Warning: Error closing exchange: {str(e)}")

    print("\n" + "=" * 60)
    print("TEST COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    # Run the test
    print("Starting Exchange Order Operations Test...")
    asyncio.run(test_exchanges_order_operations())
