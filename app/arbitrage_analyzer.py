import asyncio
import json
import time
from datetime import datetime
from typing import Any, Dict


class AnalyzeArbitrage:

    def __init__(self, last_prices_collection=None, settings=None, logger=None):
        self.last_prices_collection = last_prices_collection or []
        self.settings = settings
        self.logger = logger
        self.input_file = self.settings.arbitrage_input_file
        self.output_file = self.settings.arbitrage_output_file
        self.symbols = self.settings.symbols
        self.interval = self.settings.arbitrage_interval

        self.volume_trade = self.settings.arbitrage_volume_trade
        self.save_to_file = self.settings.arbitrage_save_to_file or False

    def _get_last_prices_per_exchange(self, entries, target_ts):
        last: Dict[str, Any] = {}
        for entry in entries:
            if isinstance(entry, str):
                try:
                    entry = json.loads(entry)
                except Exception:
                    continue
            exch = entry.get("exchange")
            label = entry.get("label")
            ts = entry.get("timestamp")
            if exch and label and label.startswith("future") and ts and ts <= target_ts:
                if exch not in last or last[exch]["timestamp"] < ts:
                    last[exch] = entry
        return last

    def _calculate_arbitrage_result(self, last_prices, symbol, timestamp, is_realtime=True):
        if not last_prices:
            return None

        if is_realtime:
            dt = datetime.utcnow().replace(microsecond=0).strftime("%Y-%m-%d %H:%M:%S")
        else:
            dt = datetime.utcfromtimestamp(timestamp // 1000).strftime("%Y-%m-%d %H:%M:%S")

        result = {
            "symbol": symbol,
            "datetime": dt,
            "exchange_future": [
                {
                    "exchange": exch,
                    "timestamp": entry["timestamp"],
                    "ask": entry["ask"],
                    "bid": entry["bid"],
                }
                for exch, entry in last_prices.items()
                if entry.get("bid") and entry.get("ask")
            ],
        }

        bids = [(exch, entry["timestamp"], entry["bid"]) for exch, entry in last_prices.items() if entry.get("bid")]
        asks = [(exch, entry["timestamp"], entry["ask"]) for exch, entry in last_prices.items() if entry.get("ask")]

        if not bids or not asks:
            return None

        max_bid = max(bids, key=lambda x: x[2][0])
        min_ask = min(asks, key=lambda x: x[2][0])
        price_diff = max_bid[2][0] - min_ask[2][0]
        price_diff_perc = price_diff / min_ask[2][0] if min_ask[2][0] else 0
        max_volume = min(max_bid[2][1], min_ask[2][1])
        medium_price = (max_bid[2][0] + min_ask[2][0]) / 2
        bid = max_bid[2]
        ask = min_ask[2]

        volume_trade = self.volume_trade

        # Correct profit calculation
        bid_profit = volume_trade * ((bid[0] - medium_price) / medium_price)
        ask_profit = volume_trade * ((medium_price - ask[0]) / ask[0])
        pls = bid_profit + ask_profit

        result.update(
            {
                "bid": [round(bid[0], 2), round(bid[1], 4)],
                "ask": [round(ask[0], 2), round(ask[1], 4)],
                "price_diff": round(price_diff, 4),
                "price_diff_perc": round(price_diff_perc, 4),
                "max_volume": round(max_volume, 4),
                "medium_price": round(medium_price, 2),
                "volume_trade": round(volume_trade, 4),
                "bid_profit": round(bid_profit, 4),
                "ask_profit": round(ask_profit, 4),
                "pls": round(pls, 4),
            }
        )

        return result

    def _arbitrage_key(self, result):
        return (
            result.get("symbol"),
            result.get("datetime"),
            round(result.get("medium_price", 0), 2),
            round(result.get("price_diff", 0), 2),
            round(result.get("volume_trade", 0), 6),
        )

    async def run(self):
        results = []
        seen = set()

        # Only read from file if save_to_file is True
        if self.save_to_file:
            try:
                with open(self.output_file, encoding="utf-8") as f:
                    results = json.load(f)
                    for r in results:
                        seen.add(self._arbitrage_key(r))
                self.logger.info(f"Loaded {len(results)} existing arbitrage results from {self.output_file}")
            except Exception:
                results = []
                seen = set()
                self.logger.info("No existing arbitrage results found, starting fresh")
        else:
            self.logger.info("File reading disabled (save_to_file=False). Starting with empty results.")
            results = []
            seen = set()

        # First run: analyze all seconds in collection
        if self.last_prices_collection is not None and not results:
            entries = []
            for e in self.last_prices_collection:
                if isinstance(e, dict):
                    entries.append(e)
                elif isinstance(e, str):
                    try:
                        d = json.loads(e)
                        if isinstance(d, dict):
                            entries.append(d)
                    except Exception:
                        continue

            all_ts = sorted({e["timestamp"] // 1000 * 1000 for e in entries if "timestamp" in e})

            for sec in all_ts:
                for symbol in self.symbols:
                    last_prices = self._get_last_prices_per_exchange(entries, sec)
                    result = self._calculate_arbitrage_result(last_prices, symbol, sec, is_realtime=False)

                    if result:
                        key = self._arbitrage_key(result)
                        if key not in seen:
                            results.append(result)
                            seen.add(key)

            if self.save_to_file:
                with open(self.output_file, "w", encoding="utf-8") as f:
                    json.dump(results, f, indent=2, ensure_ascii=False, separators=(",", ": "))
                self.logger.info(f"Arbitrage analysis saved to {self.output_file}")

        # Normal mode (current second)
        while True:
            try:
                if self.last_prices_collection is not None:
                    entries = self.last_prices_collection
                else:
                    await asyncio.sleep(self.interval)
                    continue

                now = int(time.time() * 1000)
                now_sec = now // 1000 * 1000

                for symbol in self.symbols:
                    last_prices = self._get_last_prices_per_exchange(entries, now_sec)
                    result = self._calculate_arbitrage_result(last_prices, symbol, now_sec, is_realtime=True)

                    if result:
                        key = self._arbitrage_key(result)
                        if key not in seen:
                            results.append(result)
                            seen.add(key)

                if self.save_to_file:
                    with open(self.output_file, "w", encoding="utf-8") as f:
                        json.dump(
                            results,
                            f,
                            indent=2,
                            ensure_ascii=False,
                            separators=(",", ": "),
                        )
                    self.logger.debug(f"Arbitrage analysis updated in {self.output_file}")

            except Exception as e:
                self.logger.error(f"Error in arbitrage analysis: {e}")

            await asyncio.sleep(self.interval)
