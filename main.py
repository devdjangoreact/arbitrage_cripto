import asyncio
import traceback

from app.arbitrage_analyzer import AnalyzeArbitrage
from app.exchanges_ws import ExchangesWS
from app.token_analyzer import TokensAnalyzer
from app.web_server import WebServer
from desktop.main import DesktopApp
from utils.logger import get_logger
from utils.settings import get_settings


async def main():
    # Load configuration using settings (environment is initialized automatically)
    settings = get_settings()

    # Get symbols from settings
    symbols = settings.symbols

    # Initialize logger
    logger = get_logger()

    # Initialize WebSocket exchanges
    ws_exchanges = ExchangesWS(logger=logger, settings=settings)

    # Initialize arbitrage analyzer with settings parameters
    analyzer = AnalyzeArbitrage(
        last_prices_collection=ws_exchanges.last_prices,
        settings=settings,
        logger=logger,
    )

    # Initialize tokens analyzer with settings parameters
    tokens_analyzer = TokensAnalyzer(
        last_prices_collection=ws_exchanges.last_prices,
        settings=settings,
        logger=logger,
    )

    try:
        # Prepare tasks
        tasks = []
        tasks.append(ws_exchanges.stream_futures(symbols))
        tasks.append(analyzer.run())
        tasks.append(tokens_analyzer.run(interval=settings.tokens_interval))

        # Add web server task if enabled
        if settings.web_server:
            web_host = settings.web_server_host
            web_port = settings.web_server_port
            web_server = WebServer(
                host=web_host,
                port=web_port,
                last_prices_collection=ws_exchanges.last_prices,
                save_to_file=settings.tokens_save_to_file,
                tokens_analyzer=tokens_analyzer,
            )
            logger.info(f"Web server enabled on {web_host}:{web_port}")
            tasks.append(web_server.start())

        if settings.desktop:
            desktop_app = DesktopApp()
            tasks.append(desktop_app.run())
            logger.info("Desktop app enabled")

        # Start all tasks in parallel
        await asyncio.gather(*tasks)
    except Exception as e:
        logger.error(f"Main error: {e}")
        logger.error(traceback.format_exc())
    finally:
        for ex in ws_exchanges.exchanges.values():
            await ex.close()


if __name__ == "__main__":
    # Run main with web server options
    asyncio.run(main())
