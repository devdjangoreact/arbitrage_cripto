import json
from datetime import datetime

from app.exchanges_ws import ExchangesWS
from utils.logger import MultiLogger
from utils.settings import Settings, get_settings


def get_exchanges_symbols() -> dict:
    with open(get_settings()._exchanges_symbols_path, encoding="utf-8") as f:
        return json.load(f)


def update_exchanges_symbols(new_data) -> dict:
    with open(get_settings()._exchanges_symbols_path, "w", encoding="utf-8") as f:
        json.dump(new_data, f, indent=4)
    return new_data


async def exchanges_symbols(
    ws_exchanges: ExchangesWS,
    filter: bool = False,
    update: bool = False,
    logger: MultiLogger = None,
) -> dict:
    """Exchanges symbols by settings."""

    current_data = get_exchanges_symbols()

    if current_data.get("date_update") < datetime.now().timestamp() - 3600 or update:
        new_data = await ws_exchanges.get_all_symbols_by_exchanges()

        result_data = {}
        result_data["list"] = []
        result_data["ignore"] = []
        if filter:
            # Ignore symbols

            symbols_exchanges = []
            for exchange, symbols_list in new_data.items():
                for symbols_data in symbols_list:
                    symbol = symbols_data.get("symbol")
                    item = [element for element in symbols_exchanges if element.get("symbol") == symbol]
                    if item:
                        item[0]["exchanges"].append(exchange)
                    else:
                        item = {"symbol": symbol, "exchanges": [exchange]}
                        symbols_exchanges.append(item)

            for exchange, symbols_list in new_data.items():
                if not result_data.get(exchange):
                    result_data[exchange] = []
                for symbols_data in symbols_list:
                    symbol = symbols_data.get("symbol")
                    item = [element for element in symbols_exchanges if element.get("symbol") == symbol][0]
                    if len(item.get("exchanges", [])) > 1 and symbol not in current_data.get("ignore", []):
                        result_data[exchange].append(symbol)
                    if symbol not in result_data.get("list", []):
                        result_data["list"].append(symbol)

        result_data["ignore"] = current_data.get("ignore", [])
        result_data["date_update"] = datetime.now().timestamp()
        update_exchanges_symbols(result_data)
        logger.success("Exchanges symbols updated")
        return result_data

    return current_data


def exchanges_symbols_trades(
    new_data: dict, settings: Settings, filter: bool = False, update: bool = False, logger: MultiLogger = None
) -> dict:
    """Exchanges symbols trades by settings."""
    with open(settings._exchanges_symbols_trades_path, encoding="utf-8") as f:
        current_data = json.load(f)

    if filter:
        for exchange, symbols_data in new_data.items():
            for symbol, trades_data in symbols_data.items():
                for interval, trades in trades_data.items():
                    for trade in trades:
                        current_data[exchange][symbol][interval][trade] = trade
    if update:
        for exchange, symbols_data in new_data.items():
            current_data[exchange] = symbols_data

    with open(settings._exchanges_symbols_trades_path, "w", encoding="utf-8") as f:
        json.dump(current_data, f, indent=4)
    logger.success(f"Exchanges symbols trades updated: {current_data}")
    return current_data
