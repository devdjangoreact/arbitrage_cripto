import argparse
import asyncio
import traceback

from app.arbitrage_analyzer import AnalyzeArbitrage
from app.exchanges_ws import ExchangesWS
from app.token_analyzer import TokensAnalyzer
from app.web_server import WebServer
from utils.logger import get_logger
from utils.settings import get_settings


async def main(enable_web_server=False, web_host="0.0.0.0", web_port=8000):
    # Load configuration using settings (environment is initialized automatically)
    settings = get_settings()

    # Get symbols from settings
    symbols = settings.symbols

    # Initialize logger
    logger = get_logger()

    save_to_file = False

    # Initialize WebSocket exchanges
    ws_exchanges = ExchangesWS(logger=logger, save_to_file=save_to_file)

    # Initialize arbitrage analyzer with settings parameters
    analyzer = AnalyzeArbitrage(
        input_file=settings.arbitrage_input_file,
        output_file=settings.arbitrage_output_file,
        symbols=symbols,
        interval=settings.arbitrage_interval,
        last_prices_collection=ws_exchanges.last_prices,
        volume_trade=settings.arbitrage_volume_trade,
        save_to_file=save_to_file,
    )

    # Initialize tokens analyzer with settings parameters
    tokens_analyzer = TokensAnalyzer(
        last_prices_collection=ws_exchanges.last_prices,
        output_path=settings.tokens_output_path,
        test_mode=settings.tokens_test_mode,
        periods=settings.tokens_periods,
        thresholds=settings.tokens_thresholds,
        save_to_file=save_to_file,
        symbols=symbols,
    )

    # Initialize web server if enabled
    web_server = None
    if enable_web_server:
        web_server = WebServer(
            host=web_host,
            port=web_port,
            last_prices_collection=ws_exchanges.last_prices,
            save_to_file=settings.tokens_save_to_file,
            tokens_analyzer=tokens_analyzer,
        )
        logger.info(f"Web server enabled on {web_host}:{web_port}")

    try:
        # Prepare tasks
        tasks = [
            ws_exchanges.stream_futures(symbols),
            analyzer.run(),
            tokens_analyzer.run(interval=settings.tokens_interval),
        ]

        # Add web server task if enabled
        if web_server:
            tasks.append(web_server.start())

        # Start all tasks in parallel
        await asyncio.gather(*tasks)
    except Exception as e:
        logger.error(f"Main error: {e}")
        logger.error(traceback.format_exc())
    finally:
        for ex in ws_exchanges.exchanges.values():
            await ex.close()


if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Crypto Arbitrage Analyzer")
    parser.add_argument("--web", action="store_true", help="Enable web server")
    parser.add_argument("--web-host", default="0.0.0.0", help="Web server host (default: 0.0.0.0)")
    parser.add_argument("--web-port", type=int, default=8000, help="Web server port (default: 8000)")

    args = parser.parse_args()

    # Run main with web server options
    asyncio.run(main(enable_web_server=args.web, web_host=args.web_host, web_port=args.web_port))
