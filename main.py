import asyncio
import traceback

from app.arbitrage_analyzer import AnalyzeArbitrage
from app.token_analyzer import TokensAnalyzer
from exchanges_ws import ExchangesWS
from logger import get_logger
from settings import get_settings


async def main():
    # Load configuration using settings
    settings = get_settings()

    # Extract symbols from settings
    symbol = settings.spot_symbol
    future_symbol = settings.future_symbol

    # Initialize logger
    logger = get_logger()

    # Initialize WebSocket exchanges
    ws_exchanges = ExchangesWS(logger=logger)

    # Initialize arbitrage analyzer with settings parameters
    analyzer = AnalyzeArbitrage(
        input_file=settings.arbitrage_input_file,
        output_file=settings.arbitrage_output_file,
        symbol=settings.arbitrage_symbol,
        interval=settings.arbitrage_interval,
        last_prices_collection=ws_exchanges.last_prices,
        volume_trade=settings.arbitrage_volume_trade,
    )

    # Initialize tokens analyzer with settings parameters
    tokens_analyzer = TokensAnalyzer(
        last_prices_collection=ws_exchanges.last_prices,
        output_path=settings.tokens_output_path,
        test_mode=settings.tokens_test_mode,
        periods=settings.tokens_periods,
        thresholds=settings.tokens_thresholds,
    )

    try:
        # Start WebSocket streams and analyzers in parallel
        await asyncio.gather(
            ws_exchanges.stream_futures(symbol, future_symbol),
            analyzer.run(),
            tokens_analyzer.run(
                interval=settings.tokens_interval
            ),  # Use interval from settings
        )
    except Exception as e:
        logger.error(f"Main error: {e}")
        logger.error(traceback.format_exc())
    finally:
        for ex in ws_exchanges.exchanges.values():
            await ex.close()


if __name__ == "__main__":
    asyncio.run(main())
