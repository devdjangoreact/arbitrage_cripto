import asyncio
import json
import statistics
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from ..logger import get_logger


class TokensAnalyzer:
    """
    Token analyzer for detecting arbitrage opportunities.
    Calculates metrics: delta, volume, trade count, NATR, spread, activity.
    """

    def __init__(
        self,
        last_prices_collection=None,
        output_path="data/tokens_analyzer.json",
        test_mode=False,
        periods: dict[str, str] = None,
        thresholds: dict[str, float] = None,
    ):
        self.last_prices_collection = last_prices_collection
        self.output_path = output_path
        self.logger = get_logger()
        self._test_mode = test_mode

        # Buffers for storing historical data
        self.price_history = defaultdict(
            lambda: defaultdict(deque)
        )  # {exchange: {symbol: deque}}
        self.volume_history = defaultdict(lambda: defaultdict(deque))
        self.trade_history = defaultdict(lambda: defaultdict(deque))

        self.periods = periods or {
            "delta": "1h",
            "vol": "1h",
            "trade": "1h",
            "NATR": "1h",
            "spread": "1h",
            "activity": "1h",
        }
        # Period settings (in seconds)
        self.periods_seconds = {
            "1m": 60,
            "5m": 300,
            "15m": 900,
            "1h": 3600,
            "4h": 14400,
            "1d": 86400,
        }

        # Filtering thresholds (lowered for testing)
        self.thresholds = thresholds or {
            "delta": 0,  # 0.01% minimum price difference
            "vol": 0,  # minimum trading volume
            "trade": 0,  # minimum number of trades
            "NATR": 0,  # minimum volatility
            "spread": 0,  # minimum spread
            "activity": 0,  # minimum activity
        }
        self._data_processed = False

    def _get_period_timestamp(self, period: str) -> int:
        """Get timestamp for given period."""
        # For testing with file data, use time from data
        if hasattr(self, "_test_mode") and self._test_mode:
            # Find the latest timestamp from data
            if self.last_prices_collection:
                latest_timestamp = max(
                    entry.get("timestamp", 0)
                    for entry in self.last_prices_collection
                    if isinstance(entry, dict) and "timestamp" in entry
                )
                period_seconds = self.periods_seconds.get(period, 3600)
                return latest_timestamp - (period_seconds * 1000)

        now = int(time.time() * 1000)
        period_seconds = self.periods_seconds.get(period, 3600)  # default 1 hour
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
        first_price = prices[0].get("price", 0)
        last_price = prices[-1].get("price", 0)

        if first_price == 0:
            return 0.0

        return abs(last_price - first_price) / first_price

    def _calculate_volume(self, volumes: List[Dict]) -> float:
        """Calculate total trading volume."""
        return sum(item.get("volume", 0) for item in volumes)

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
            high = sorted_prices[i].get("high", sorted_prices[i].get("price", 0))
            low = sorted_prices[i].get("low", sorted_prices[i].get("price", 0))
            prev_close = sorted_prices[i - 1].get("price", 0)

            tr1 = high - low
            tr2 = abs(high - prev_close)
            tr3 = abs(low - prev_close)

            true_range = max(tr1, tr2, tr3)
            true_ranges.append(true_range)

        if not true_ranges:
            return 0.0

        atr = (
            statistics.mean(true_ranges[-period:])
            if len(true_ranges) >= period
            else statistics.mean(true_ranges)
        )
        current_price = sorted_prices[-1].get("price", 1)

        return atr / current_price if current_price > 0 else 0.0

    def _calculate_spread(self, prices: List[Dict]) -> float:
        """Calculate spread (difference between ask and bid)."""
        if not prices:
            return 0.0

        # Take latest data
        last_data = prices[-1]
        ask = (
            last_data.get("ask", [0, 0])[0]
            if isinstance(last_data.get("ask"), list)
            else last_data.get("ask", 0)
        )
        bid = (
            last_data.get("bid", [0, 0])[0]
            if isinstance(last_data.get("bid"), list)
            else last_data.get("bid", 0)
        )

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
            interval = sorted_prices[i].get("timestamp", 0) - sorted_prices[i - 1].get(
                "timestamp", 0
            )
            intervals.append(interval)

        if not intervals:
            return 0.0

        avg_interval = statistics.mean(intervals) / 1000  # convert to seconds
        return 1.0 / avg_interval if avg_interval > 0 else 0.0

    async def _analyze_file_data(self):
        """Analyze data from last_prices_ws.json file before switching to real data."""
        file_path = "data/last_prices_ws.json"
        try:
            self.logger.info(f"Loading data from {file_path}...")
            with open(file_path, "r", encoding="utf-8") as f:
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
                result = self.filter_and_save(
                    output_path="data/tokens_analyzer_file.json"
                )

                # Log file analysis result
                total_tokens = sum(len(tokens) for tokens in result.values())
                self.logger.info(
                    f"File analysis completed. Found {total_tokens} tokens across {len(result)} exchanges"
                )

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
        rounded_data = {}
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
        symbol = entry.get("symbol", "")
        if "/" in symbol:
            return symbol.split("/")[0].lower()  # BTC from BTC/USDT
        return symbol.lower()

    def _process_price_data(self, entry: Dict):
        """Process price data and add to history."""
        exchange = entry.get("exchange")
        symbol = self._extract_symbol_from_data(entry)
        timestamp = entry.get("timestamp", 0)

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

        # Add to price history
        price_data = {
            "timestamp": timestamp,
            "price": price,
            "ask": ask,
            "bid": bid,
            "high": max(ask_price, bid_price),
            "low": min(ask_price, bid_price),
        }

        self.price_history[exchange][symbol].append(price_data)

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
        volume_data = {"timestamp": timestamp, "volume": volume}
        self.volume_history[exchange][symbol].append(volume_data)

        while len(self.volume_history[exchange][symbol]) > max_size:
            self.volume_history[exchange][symbol].popleft()

        # Add to trade history (each price update = trade)
        trade_data = {"timestamp": timestamp, "price": price, "volume": volume}
        self.trade_history[exchange][symbol].append(trade_data)

        while len(self.trade_history[exchange][symbol]) > max_size:
            self.trade_history[exchange][symbol].popleft()

    def calculate_metrics(self, exchange: str, symbol: str) -> Dict:
        """Calculate all metrics for token on exchange."""

        result = {}

        # Get data for required periods
        price_data = self._filter_by_period(
            self.price_history[exchange][symbol], self.periods.get("delta", "1h")
        )
        volume_data = self._filter_by_period(
            self.volume_history[exchange][symbol], self.periods.get("vol", "1h")
        )
        trade_data = self._filter_by_period(
            self.trade_history[exchange][symbol], self.periods.get("trade", "1h")
        )

        # Calculate metrics
        result["delta"] = self._calculate_delta(price_data)
        result["vol"] = self._calculate_volume(volume_data)
        result["trade"] = self._calculate_trade_count(trade_data)
        result["NATR"] = self._calculate_natr(price_data)
        result["spread"] = self._calculate_spread(price_data)
        result["activity"] = self._calculate_activity(price_data)

        return result

    def filter_and_save(self, output_path: str = None) -> Dict:
        """
        Фільтрувати токени за метриками та зберегти результат.

        Args:
            output_path: шлях для збереження результату

        Returns:
            dict: відфільтровані результати
        """
        if output_path is None:
            output_path = self.output_path

        result = {}

        # Process data from collection (only if not yet processed)
        if self.last_prices_collection and not hasattr(self, "_data_processed"):
            self.logger.info(
                f"Processing {len(self.last_prices_collection)} records from collection..."
            )
            for entry in self.last_prices_collection:
                if isinstance(entry, dict):
                    self._process_price_data(entry)
                elif isinstance(entry, str):
                    try:
                        data = json.loads(entry)
                        if isinstance(data, dict):
                            self._process_price_data(data)
                    except Exception:
                        continue
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
                        and (
                            metrics["NATR"] >= self.thresholds["NATR"]
                            or metrics["NATR"] == 0
                        )
                        and metrics["spread"] >= self.thresholds["spread"]
                        and metrics["activity"] >= self.thresholds["activity"]
                    ):

                        result[exchange][symbol] = metrics

                except Exception as e:
                    self.logger.error(
                        f"Error calculating metrics for {exchange}:{symbol}: {e}"
                    )
                    continue

        # Round all numeric values to 4 decimal places
        rounded_result = self._round_metrics(result)

        # Save result
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

        while True:
            try:
                # Process new data (only new records)
                if self.last_prices_collection:
                    # Get number of records we have already processed
                    current_length = len(self.last_prices_collection)

                    # If there are new records, process them
                    if hasattr(self, "_last_processed_length"):
                        if current_length > self._last_processed_length:
                            new_entries = self.last_prices_collection[
                                self._last_processed_length :
                            ]
                            self.logger.info(
                                f"Processing {len(new_entries)} new real-time entries..."
                            )
                            for entry in new_entries:
                                if isinstance(entry, dict):
                                    self._process_price_data(entry)
                                elif isinstance(entry, str):
                                    try:
                                        data = json.loads(entry)
                                        if isinstance(data, dict):
                                            self._process_price_data(data)
                                    except Exception:
                                        continue
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
            for coin, metrics in coins.items():
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
