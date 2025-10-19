import asyncio
import time
from datetime import datetime, timedelta

from app.exchanges_ws import ExchangesWS
from utils.settings import get_settings


class ArbitrageFutures:
    """
    Class for managing arbitrage futures trading operations.
    Handles spread calculation, order creation, monitoring, and profit calculation.
    """

    def __init__(self, exchanges_ws: ExchangesWS, logger=None, settings=None):
        """
        Initialize the ArbitrageFutures class.

        Args:
            exchanges_ws: ExchangesWS instance for price data
            logger: Logger instance for logging
            settings: Settings instance for configuration
        """
        self.exchanges_ws = exchanges_ws
        self.logger = logger
        self.settings = settings
        self.orders_pairs = []
        self.last_prices = []
        self.data_arbitrage = []

        self._load_config()

    def _load_config(self):
        """Load configuration from mock data or use defaults."""
        try:
            import json

            with open("utils/mock_data.json") as f:
                mock_data = json.load(f)
            self.exchange_limits = mock_data.get("exchange_limits", {})
            config_params = mock_data.get("test_params", {})
        except FileNotFoundError:
            self.exchange_limits = {}
            config_params = {
                "spread_close": 0.5,
                "spread_open": 1.0,
                "spread_start": 1.5,
                "spread_end": 0.3,
                "leverage": 10,
                "amount_usdt": 100,
            }

        self.spread_close = config_params["spread_close"]
        self.spread_open = config_params["spread_open"]
        self.leverage = config_params["leverage"]
        self.amount_usdt = config_params["amount_usdt"]

    def get_last_prices(self, start_index=0, number_of_items=10):
        """
        Get last prices from exchanges_ws.last_prices.
        """
        return self.exchanges_ws.last_prices[start_index : start_index + number_of_items]

    def calculate_spread(self, prices_data=None):
        """
        Calculate current spread for the symbol.

        Args:
            prices_data: Price data to use (optional, uses exchanges_ws.last_prices if not provided)

        Returns:
            tuple: (high_price_exchange, low_price_exchange, spread, spread_percentage)
        """

        for price in prices_data:
            symbol_element = next(
                (element for element in self.data_arbitrage if element["symbol"] == price["symbol"]), None
            )
            if not symbol_element:
                symbol_element = {
                    "symbol": price["symbol"],
                    "last_prices": [],
                    "high_price": 0,
                    "low_price": 0,
                    "profit": 0,
                    "spread": 0,
                    "spread_percentage": 0,
                }
                self.data_arbitrage.append(symbol_element)
            last_prices_element = next(
                (element for element in symbol_element["last_prices"] if element["exchange"] == price["exchange"]), None
            )
            if not last_prices_element:
                last_prices_element = {"exchange": price["exchange"]}
                symbol_element["last_prices"].append(last_prices_element)
            last_prices_element["ask"] = price["ask"][0]
            last_prices_element["bid"] = price["bid"][0]

            if symbol_element["last_prices"]:

                symbol_element["high_price"] = max(symbol_element["last_prices"], key=lambda x: x["ask"])
                symbol_element["low_price"] = min(symbol_element["last_prices"], key=lambda x: x["bid"])

                high_price = symbol_element["high_price"]["ask"]
                low_price = symbol_element["low_price"]["bid"]
                symbol_element["spread"] = round(high_price - low_price, 2)
                symbol_element["spread_percentage"] = round((symbol_element["spread"] / low_price) * 100, 2)
                symbol_element["profit_100"] = self.calculate_profit(high_price, low_price)
        return self.data_arbitrage

    def calculate_profit(self, high_price, low_price):
        return round((high_price - low_price) * ((100 - self.spread_close) / 100) / low_price * 100, 2)

    def _format_prices_table(self, prices_data):
        """Format price data into compact single line format for logging."""
        if not prices_data:
            return "No price data"

        # Create compact single line format: SYMBOL: EX1:ASK/BID, EX2:ASK/BID, ...
        compact_lines = []

        # Group by symbol for compact display
        symbol_groups = {}
        for price_data in prices_data:
            symbol = price_data.get("symbol", "UNKNOWN")
            if symbol not in symbol_groups:
                symbol_groups[symbol] = []
            symbol_groups[symbol].append(price_data)

        for symbol, prices in symbol_groups.items():
            price_strs = []
            for price_data in prices:
                exchange = price_data.get("exchange", "N/A")[:6]  # Shorter exchange names
                ask_price = f"{price_data.get('ask', [0])[0]:.2f}" if price_data.get("ask") else "0.00"
                bid_price = f"{price_data.get('bid', [0])[0]:.2f}" if price_data.get("bid") else "0.00"
                price_strs.append(f"{exchange}:{ask_price}/{bid_price}")

            compact_lines.append(f"📊 {symbol}: {', '.join(price_strs)}")

        return " | ".join(compact_lines)

    def _format_arbitrage_table(self):
        """Format arbitrage analysis data into compact single line format for logging."""
        if not self.data_arbitrage:
            return "No arbitrage data"

        # Create compact format: SYMBOL:HIGH_EX:LOW_EX:SPREAD$:SPREAD%:PROFIT%:STATUS
        compact_lines = []

        for symbol_data in self.data_arbitrage:
            symbol = symbol_data.get("symbol", "N/A")[:8]

            # Get high and low exchange info
            high_price_info = symbol_data.get("high_price", {})
            low_price_info = symbol_data.get("low_price", {})

            high_ex = high_price_info.get("exchange", "N/A")[:6]
            low_ex = low_price_info.get("exchange", "N/A")[:6]

            spread = f"{symbol_data.get('spread', 0):.2f}"
            spread_pct = f"{symbol_data.get('spread_percentage', 0):.2f}"
            profit = f"{symbol_data.get('profit_100', 0):.2f}"

            # Determine if arbitrage opportunity exists
            status = "OPPORTUNITY" if symbol_data.get("spread_percentage", 0) > self.spread_open else "WAITING"

            compact_lines.append(
                f"🔄 {symbol}:[{high_ex}:{low_ex}]:spread-${spread}({spread_pct}%):profit-${profit}:{status}"
            )

        return " | ".join(compact_lines)

    def _format_orders_table(self, orders_pair=None):
        """Format active orders into compact single line format for logging."""
        if not orders_pair:
            if not self.orders_pairs:
                return "No active orders"
            orders_pairs = self.orders_pairs
        else:
            orders_pairs = [orders_pair]

        # Create compact format: SYMBOL:LONG_EX:SHORT_EX:AMOUNT:LONG$:SHORT$:PROFIT$:STATUS
        compact_lines = []

        for orders_pair in orders_pairs:

            symbol = orders_pair.get("symbol", "N/A")[:8]

            long_order = orders_pair.get("long_order", {})
            short_order = orders_pair.get("short_order", {})

            long_ex = long_order.get("exchange", "N/A")[:6]
            short_ex = short_order.get("exchange", "N/A")[:6]

            amount = f"{orders_pair.get('amount', 0):.4f}"
            long_price = f"{long_order.get('price', 0):.2f}"
            short_price = f"{short_order.get('price', 0):.2f}"
            profit = f"{orders_pair.get('profit', 0):.2f}"

            status = "OPEN" if orders_pair.get("status") == "open" else "CLOSED"

            compact_lines.append(
                f"📋 {symbol}:[{long_ex}:${long_price}]:[{short_ex}:${short_price}]:amount-{amount}:profit-${profit}:{status}"
            )

        return " | ".join(compact_lines)

    def create_arbitrage_orders(self):
        for symbol_element in self.data_arbitrage:
            if symbol_element["spread_percentage"] > self.spread_open:
                symbol = symbol_element["symbol"]
                if not any(orders_pair["symbol"] == symbol for orders_pair in self.orders_pairs):
                    self.create_arbitrage_orders_for_symbol(symbol_element)

    def create_arbitrage_orders_for_symbol(self, symbol_element):
        """
        Create arbitrage orders for a symbol.
        """
        symbol = symbol_element["symbol"]

        high_exchange = symbol_element["high_price"]
        low_exchange = symbol_element["low_price"]
        if not high_exchange or not low_exchange:
            return

        # Get minimum order amounts for both exchanges
        high_ex_name = high_exchange["exchange"]
        low_ex_name = low_exchange["exchange"]

        min_amount_high = self.exchange_limits.get(high_ex_name, {}).get("min_amount", 0.001)
        min_amount_low = self.exchange_limits.get(low_ex_name, {}).get("min_amount", 0.001)
        max_min_amount = max(min_amount_high, min_amount_low)

        low_price = low_exchange["bid"]
        high_price = high_exchange["ask"]

        # Calculate order amount (in BTC for futures)
        order_amount = self.amount_usdt / low_price  # Base amount in BTC
        order_amount = max(order_amount, max_min_amount)  # Ensure minimum amount

        # Long order on low price exchange
        long_order = {
            "id": int(time.time() * 1000) % 1000000,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "exchange": low_ex_name,
            "symbol": symbol,
            "side": "long",
            "type": "limit",
            "open_type": "isolated",
            "leverage": self.leverage,
            "price": low_price,
            "amount": order_amount,
            "amount_usdt": self.amount_usdt,
            "fee": self.exchange_limits.get(low_ex_name, {}).get("fee", 0.001),
            "status": "open",
        }

        # Short order on high price exchange
        short_order = {
            "id": int(time.time() * 1000 + 1) % 1000000,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "exchange": high_ex_name,
            "symbol": symbol,
            "side": "short",
            "type": "limit",
            "open_type": "isolated",
            "leverage": self.leverage,
            "price": high_price,
            "amount": order_amount,
            "amount_usdt": self.amount_usdt,
            "fee": self.exchange_limits.get(high_ex_name, {}).get("fee", 0.001),
            "status": "open",
        }
        orders_pair = {
            "symbol": symbol,
            "short_order": short_order,
            "long_order": long_order,
            "status": "open",
            "amount": order_amount,
            "profit": symbol_element["profit_100"],
            "profit_long": symbol_element["profit_100"] / 2,
            "profit_short": symbol_element["profit_100"] / 2,
            "spread_percentage": symbol_element["spread_percentage"],
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "spread": symbol_element["spread"],
        }

        self.orders_pairs.append(orders_pair)

        self.logger.info(f"\n\nCREATED ORDERS: {self._format_orders_table(orders_pair)}\n")

        return orders_pair

    def calculate_profit_now_orders_pair(self, price, now_price, amount):
        return round((now_price - price) * amount * self.leverage, 2)

    def monitor_and_close_orders(self):
        """
        Monitor spread and close orders when threshold is reached.
        """
        for orders_pair in self.orders_pairs:
            if orders_pair["long_order"]["status"] == "closed" or orders_pair["short_order"]["status"] == "closed":
                continue
            symbol = orders_pair["symbol"]

            symbol_element = next((element for element in self.data_arbitrage if element["symbol"] == symbol), None)
            if symbol_element:
                last_prices = symbol_element["last_prices"]
                now_long_price = next(
                    (price for price in last_prices if price["exchange"] == orders_pair["long_order"]["exchange"]), None
                )["bid"]
                now_short_price = next(
                    (price for price in last_prices if price["exchange"] == orders_pair["short_order"]["exchange"]),
                    None,
                )["ask"]
                amount = orders_pair["amount"]

                long_order = orders_pair["long_order"]
                short_order = orders_pair["short_order"]

                short_price = short_order["price"]
                long_price = long_order["price"]

                orders_pair["profit_long"] = self.calculate_profit_now_orders_pair(long_price, now_long_price, amount)
                orders_pair["profit_short"] = self.calculate_profit_now_orders_pair(
                    short_price, now_short_price, amount
                )
                orders_pair["profit"] = orders_pair["profit_long"] + orders_pair["profit_short"]
                if symbol_element["spread_percentage"] <= self.spread_close:
                    # self.close_order(order)
                    orders_pair["status"] = "closed"
                    orders_pair["long_order"]["status"] = "closed"
                    orders_pair["short_order"]["status"] = "closed"

                    self.logger.info(f"\n\nCLOSED ORDERS: {self._format_orders_table(orders_pair)}\n")

    def sync_data_from_exchange(self):
        """
        Sync data from exchange.
        """
        # sync balance from exchange

        # sync open orders from exchange

    async def run_arbitrage(self):
        """
        Main method to run the complete arbitrage process.

        Returns:
            dict: Complete arbitrage results
        """

        self.spread_close = 1
        self.spread_open = 4
        self.leverage = 2

        print("Starting arbitrage futures trading...")
        start_index = 0
        now = datetime.now()
        next_sync_time = now
        while True:
            if now >= next_sync_time:
                # check order in exchange
                self.sync_data_from_exchange()
                next_sync_time = now + timedelta(seconds=15)

            last_prices = self.get_last_prices(start_index=start_index, number_of_items=1)
            start_index += 1
            if not last_prices:
                break

            # Filter prices for the futures symbol
            symbol_prices = [p for p in last_prices if "USDT:USDT" in p.get("symbol")]
            if not symbol_prices:
                continue
            # Log all data in compact format on single lines
            if last_prices:
                self.logger.info(f"PRICES: {self._format_prices_table(last_prices)}")
            else:
                self.logger.info("PRICES: No data")

            self.calculate_spread(last_prices)

            if self.data_arbitrage:
                self.logger.info(f"ARB: {self._format_arbitrage_table()}")

            self.create_arbitrage_orders()

            if self.orders_pairs:
                self.logger.info(f"ORDERS: {self._format_orders_table()}")

            # Monitor and close orders
            self.monitor_and_close_orders()

            # await asyncio.sleep(1)
            self.logger.info("-------------------------------------------------")


if __name__ == "__main__":
    # Run the test
    print("Starting Exchange Order Operations Test...")
    from utils.logger import get_logger

    # Initialize logger
    logger = get_logger()
    settings = get_settings()
    # Initialize ExchangesWS
    exchanges_ws = ExchangesWS(logger=logger, settings=settings)

    arbitrage = ArbitrageFutures(exchanges_ws, logger=logger)
    asyncio.run(arbitrage.run_arbitrage())
