import asyncio
import json
import statistics
import time
import traceback
from collections import deque
from datetime import datetime
from typing import Any, Dict, List, Optional


class TokensAnalyzer:
    """
    Token analyzer for detecting arbitrage opportunities.
    Calculates metrics: delta, volume, trade count, NATR, spread, activity.
    """

    def __init__(
        self,
        last_prices_collection: Optional[List[Dict[str, Any]]] = None,
        settings=None,
        logger=None,
    ):
        self.last_prices_collection = last_prices_collection or []
        self.settings = settings
        self.logger = logger
        self.output_path = self.settings.tokens_output_path
        self.test_mode = self.settings.tokens_test_mode
        self.save_to_file = self.settings.tokens_save_to_file or False
        self.symbols = self.settings.symbols
        self.periods = self.settings.tokens_periods_seconds
        self.thresholds = self.settings.tokens_thresholds
        self._data_processed = False

    def _get_period_timestamp(self, period: str) -> int:
        """Get timestamp for given period."""
        # For testing with file data, use time from data
        if hasattr(self, "test_mode") and self.test_mode:
            # Find the latest timestamp from data
            if self.last_prices_collection:
                latest_timestamp = max(
                    int(entry.get("timestamp", 0))
                    for entry in self.last_prices_collection
                    if isinstance(entry, dict) and "timestamp" in entry
                )
                period_seconds = self.periods.get(period, 3600)
                return latest_timestamp - (period_seconds * 1000)

        now = int(time.time() * 1000)
        period_seconds = self.periods.get(period, 3600)  # default 1 hour
        return now - (period_seconds * 1000)

    def _filter_by_period(self, data: deque, period: str) -> List:
        """Filter data by period."""
        cutoff_ts = self._get_period_timestamp(period)
        return [item for item in data if item.get("timestamp", 0) >= cutoff_ts]

    def _calculate_delta(self, prices: List[Dict]) -> float:
        """Calculate absolute price difference (delta)."""
        if len(prices) < 1:
            return 0.0

        if len(prices) == 1:
            # If only one point, return minimum value
            return 0.0001

        # Take first and last price in period
        first_price = float(prices[0].get("price", 0))
        last_price = float(prices[-1].get("price", 0))

        if first_price == 0:
            return 0.0

        return abs(last_price - first_price) / first_price

    def _calculate_volume(self, volumes: List[Dict]) -> float:
        """Calculate total trading volume."""
        return sum(float(item.get("volume", 0)) for item in volumes)

    def _calculate_trade_count(self, trades: List[Dict]) -> int:
        """Calculate number of trades."""
        return len(trades)

    def _calculate_natr(self, prices: List[Dict], period: int = 14) -> float:
        """Calculate Normalized Average True Range (NATR)."""
        if len(prices) < period + 1:
            return 0.0

        # Sort by time
        sorted_prices = sorted(prices, key=lambda x: x.get("timestamp", 0))

        true_ranges = []
        for i in range(1, len(sorted_prices)):
            high = float(sorted_prices[i].get("high", sorted_prices[i].get("price", 0)))
            low = float(sorted_prices[i].get("low", sorted_prices[i].get("price", 0)))
            prev_close = float(sorted_prices[i - 1].get("price", 0))

            tr1 = high - low
            tr2 = abs(high - prev_close)
            tr3 = abs(low - prev_close)

            true_range = max(tr1, tr2, tr3)
            true_ranges.append(true_range)

        if not true_ranges:
            return 0.0

        atr = statistics.mean(true_ranges[-period:]) if len(true_ranges) >= period else statistics.mean(true_ranges)
        current_price = float(sorted_prices[-1].get("price", 1))

        return atr / current_price if current_price > 0 else 0.0

    def _calculate_spread(self, prices: List[Dict]) -> float:
        """Calculate spread (difference between ask and bid)."""
        if not prices:
            return 0.0

        # Take latest data
        last_data = prices[-1]
        ask_val = last_data.get("ask")
        ask = float(ask_val[0] if isinstance(ask_val, list) else ask_val if ask_val is not None else 0)
        bid_val = last_data.get("bid")
        bid = float(bid_val[0] if isinstance(bid_val, list) else bid_val if bid_val is not None else 0)

        if ask == 0 or bid == 0:
            return 0.0

        return (ask - bid) / ask

    def _calculate_activity(self, prices: List[Dict]) -> float:
        """Calculate activity (price update frequency)."""
        if len(prices) < 2:
            return 0.0

        # Sort by time
        sorted_prices = sorted(prices, key=lambda x: x.get("timestamp", 0))

        # Calculate average interval between updates
        intervals = []
        for i in range(1, len(sorted_prices)):
            interval = sorted_prices[i].get("timestamp", 0) - sorted_prices[i - 1].get("timestamp", 0)
            intervals.append(interval)

        if not intervals:
            return 0.0

        avg_interval = statistics.mean(intervals) / 1000  # convert to seconds
        return 1.0 / avg_interval if avg_interval > 0 else 0.0

    async def _analyze_file_data(self):
        """Analyze data from last_prices_ws.json file before switching to real data."""
        # Only read from file if save_to_file is True
        if not self.save_to_file:
            self.logger.info("File reading disabled (save_to_file=False). Skipping file analysis.")
            return

        file_path = "data/last_prices_ws.json"
        try:
            self.logger.info(f"Loading data from {file_path}...")
            with open(file_path) as f:
                file_data = []
                for line in f:
                    if line.strip():
                        try:
                            entry = json.loads(line)
                            file_data.append(entry)
                        except json.JSONDecodeError:
                            continue

            if file_data:
                self.logger.info(f"Loaded {len(file_data)} records from file")

                # Process data from file
                for entry in file_data:
                    if isinstance(entry, dict):
                        self._process_price_data(entry)

                # Perform analysis with data from file
                self.logger.info("Analyzing file data...")
                result = self.filter_and_save(output_path="data/tokens_analyzer_file.json")

                # Log file analysis result
                total_tokens = sum(len(tokens) for tokens in result.values())
                self.logger.info(f"File analysis completed. Found {total_tokens} tokens across {len(result)} exchanges")

                for exchange, tokens in result.items():
                    if tokens:
                        self.logger.info("  %s: %d tokens", exchange, len(tokens))
                        for token, metrics in tokens.items():
                            self.logger.info(
                                "    %s: delta=%.4f, vol=%.4f, trades=%d",
                                token,
                                metrics["delta"],
                                metrics["vol"],
                                metrics["trade"],
                            )
            else:
                self.logger.warning(f"No data found in {file_path}")

        except FileNotFoundError:
            self.logger.warning(f"File {file_path} not found. Skipping file analysis.")
        except Exception as e:
            self.logger.error(f"Error analyzing file data: {e}")

    def _round_metrics(self, data: Dict) -> Dict:
        """Round all numeric values in results to 4 decimal places."""
        rounded_data: Dict[str, Any] = {}
        for exchange, tokens in data.items():
            rounded_data[exchange] = {}
            for symbol, metrics in tokens.items():
                rounded_data[exchange][symbol] = {}
                for key, value in metrics.items():
                    if isinstance(value, (int, float)):
                        rounded_data[exchange][symbol][key] = round(value, 4)
                    else:
                        rounded_data[exchange][symbol][key] = value
        return rounded_data

    def _extract_symbol_from_data(self, entry: Dict) -> str:
        """Extract token symbol from data record."""
        symbol = str(entry.get("symbol", ""))
        # Check if this symbol is in our symbols list
        if symbol in self.symbols:
            if "/" in symbol:
                return symbol.split("/")[0].lower()  # BTC from BTC/USDT
            return symbol.lower()
        return ""

    def _process_price_data(self, entry: Dict):
        """Process price data and add to history."""
        exchange = entry.get("exchange")
        symbol = self._extract_symbol_from_data(entry)

        if not exchange or not symbol:
            return

        # Extract price (average of ask and bid)
        ask = entry.get("ask")
        bid = entry.get("bid")

        if isinstance(ask, list) and len(ask) >= 1:
            ask_price = ask[0]
        elif isinstance(ask, (int, float)):
            ask_price = ask
        else:
            ask_price = 0

        if isinstance(bid, list) and len(bid) >= 1:
            bid_price = bid[0]
        elif isinstance(bid, (int, float)):
            bid_price = bid
        else:
            bid_price = 0

        if ask_price > 0 and bid_price > 0:
            price = (ask_price + bid_price) / 2
        elif ask_price > 0:
            price = ask_price
        elif bid_price > 0:
            price = bid_price
        else:
            return

        self.price_history[exchange][symbol].append({"price": price, "timestamp": int(time.time() * 1000)})

        # Limit buffer size (keep data for last 24 hours)
        max_size = 86400  # 24 hours in seconds
        while len(self.price_history[exchange][symbol]) > max_size:
            self.price_history[exchange][symbol].popleft()

        # Add to volume history (use bid volume as proxy)
        if isinstance(bid, list) and len(bid) >= 2:
            volume = bid[1]
        elif isinstance(ask, list) and len(ask) >= 2:
            volume = ask[1]
        else:
            volume = 0

        # Always add volume (even if 0)
        self.volume_history[exchange][symbol].append({"volume": volume, "timestamp": int(time.time() * 1000)})

        while len(self.volume_history[exchange][symbol]) > max_size:
            self.volume_history[exchange][symbol].popleft()

        # Add to trade history (each price update = trade)
        self.trade_history[exchange][symbol].append({"count": 1, "timestamp": int(time.time() * 1000)})

        while len(self.trade_history[exchange][symbol]) > max_size:
            self.trade_history[exchange][symbol].popleft()

    def calculate_metrics(self, exchange: str, symbol: str) -> Dict:
        """Calculate all metrics for token on exchange."""

        result = {}

        # Get data for required periods
        price_data = self._filter_by_period(self.price_history[exchange][symbol], self.periods.get("delta", "1h"))
        volume_data = self._filter_by_period(self.volume_history[exchange][symbol], self.periods.get("vol", "1h"))
        trade_data = self._filter_by_period(self.trade_history[exchange][symbol], self.periods.get("trade", "1h"))

        # Calculate metrics
        result["delta"] = self._calculate_delta(price_data)
        result["vol"] = self._calculate_volume(volume_data)
        result["trade"] = self._calculate_trade_count(trade_data)
        result["NATR"] = self._calculate_natr(price_data)
        result["spread"] = self._calculate_spread(price_data)
        result["activity"] = self._calculate_activity(price_data)

        return result

    def filter_and_save(self, output_path: Optional[str] = None) -> Dict:
        """
        Фільтрувати токени за метриками та зберегти результат.

        Args:
            output_path: шлях для збереження результату

        Returns:
            dict: відфільтровані результати
        """
        if output_path is None:
            output_path = self.output_path

        result: Dict[str, Any] = {}

        # Process data from collection (only if not yet processed)
        if self.last_prices_collection and not hasattr(self, "_data_processed"):
            self.logger.info(f"Processing {len(self.last_prices_collection)} records from collection...")
            for entry in self.last_prices_collection:
                self._process_price_data(entry)
            self._data_processed = True

        # Calculate metrics for all exchanges and tokens
        for exchange in self.price_history:
            result[exchange] = {}

            for symbol in self.price_history[exchange]:
                try:
                    metrics = self.calculate_metrics(exchange, symbol)

                    # Filter by thresholds (NATR can be 0, so check only if > 0)
                    if (
                        metrics["delta"] >= self.thresholds["delta"]
                        and metrics["vol"] >= self.thresholds["vol"]
                        and metrics["trade"] >= self.thresholds["trade"]
                        and (metrics["NATR"] >= self.thresholds["NATR"] or metrics["NATR"] == 0)
                        and metrics["spread"] >= self.thresholds["spread"]
                        and metrics["activity"] >= self.thresholds["activity"]
                    ):

                        result[exchange][symbol] = metrics

                except Exception as e:
                    self.logger.error(f"Error calculating metrics for {exchange}:{symbol}: {traceback.format_exc(e)}")
                    continue

        # Round all numeric values to 4 decimal places
        rounded_result = self._round_metrics(result)

        # Save result only if save_to_file is True
        if self.save_to_file:
            try:
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(rounded_result, f, indent=2, ensure_ascii=False)
                self.logger.info(f"Tokens analysis saved to {output_path}")
            except Exception as e:
                self.logger.error(f"Error saving tokens analysis: {e}")

        return result

    async def run(self, interval: int = 60):
        """Run token analyzer in loop."""
        self.logger.info("Starting tokens analyzer...")

        # First analyze data from last_prices_ws.json file
        await self._analyze_file_data()

        # Wait a bit for new data to accumulate
        await asyncio.sleep(5)

        # Start a separate task for 10-second logging
        asyncio.create_task(self._log_data_every_10_seconds())

        while True:
            try:
                # Process new data (only new records)
                if self.last_prices_collection:
                    # Get number of records we have already processed
                    current_length = len(self.last_prices_collection)

                    # If there are new records, process them
                    if hasattr(self, "_last_processed_length"):
                        if current_length > self._last_processed_length:
                            new_entries = self.last_prices_collection[self._last_processed_length :]
                            self.logger.info(f"Processing {len(new_entries)} new real-time entries...")
                            for entry in new_entries:
                                self._process_price_data(entry)
                    else:
                        # Set initial length after file processing
                        self._last_processed_length = current_length

                # Filter and save results
                result = self.filter_and_save()

                # Log result
                total_tokens = sum(len(tokens) for tokens in result.values())
                self.logger.info(
                    f"Tokens analysis completed. Found {total_tokens} tokens across {len(result)} exchanges"
                )

                await asyncio.sleep(interval)

            except Exception as e:
                self.logger.error(f"Error in tokens analyzer: {e}")
                await asyncio.sleep(interval)

    async def _log_data_every_10_seconds(self):
        """Log token analyzer data every 10 seconds."""
        while True:
            try:
                await asyncio.sleep(10)  # Wait 10 seconds

                # Get current data
                result = self.filter_and_save()

                if result:
                    total_tokens = sum(len(tokens) for tokens in result.values())
                    self.logger.info("=" * 60)
                    self.logger.info(f"📊 TOKEN ANALYZER DATA UPDATE - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    self.logger.info(f"Total tokens: {total_tokens} across {len(result)} exchanges")

                    # Log details for each exchange
                    for exchange, tokens in result.items():
                        if tokens:
                            self.logger.info(f"  📈 {exchange.upper()}: {len(tokens)} tokens")

                            # Log top 3 tokens by delta for each exchange
                            sorted_tokens = sorted(
                                tokens.items(),
                                key=lambda x: x[1].get("delta", 0),
                                reverse=True,
                            )
                            for i, (symbol, metrics) in enumerate(sorted_tokens[:3]):
                                self.logger.info(
                                    f"    {i+1}. {symbol.upper()}: "
                                    f"Δ={metrics.get('delta', 0):.4f}, "
                                    f"Vol={metrics.get('vol', 0):.2f}, "
                                    f"Trades={metrics.get('trade', 0)}, "
                                    f"NATR={metrics.get('NATR', 0):.4f}"
                                )

                    self.logger.info("=" * 60)
                else:
                    self.logger.info("📊 No token data available for logging")

            except Exception as e:
                self.logger.error(f"Error in 10-second logging: {e}")
                await asyncio.sleep(10)


# Function for backward compatibility
def filter_and_save(data, output_path="data/tokens_analyzer.json"):
    """
    Function for backward compatibility.
    Creates analyzer and processes data.
    """
    analyzer = TokensAnalyzer()

    # If data is provided, process it
    if data:
        for exchange, coins in data.items():
            for coin, _ in coins.items():
                # Create fake data for testing
                fake_entry = {
                    "exchange": exchange,
                    "symbol": f"{coin.upper()}/USDT",
                    "timestamp": int(time.time() * 1000),
                    "ask": [100.0, 1.0],
                    "bid": [99.0, 1.0],
                }
                analyzer._process_price_data(fake_entry)

    return analyzer.filter_and_save(output_path)
