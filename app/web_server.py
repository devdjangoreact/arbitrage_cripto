import asyncio
import json
import os
from datetime import datetime

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from utils.logger import get_logger


class FilterUpdate(BaseModel):
    periods: dict = {}
    thresholds: dict = {}


class WebServer:
    """Async web server for system status monitoring."""

    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 8000,
        last_prices_collection=None,
        save_to_file=True,
        tokens_analyzer=None,
    ):
        self.host = host
        self.port = port
        self.logger = get_logger()
        self.app = FastAPI(title="Crypto Arbitrage Analyzer", version="1.0.0")
        self.templates = Jinja2Templates(directory="templates")

        # Mount static files from templates directory
        self.app.mount("/templates", StaticFiles(directory="templates"), name="templates")

        # Mount static files from utils directory to serve JSON files
        self.app.mount("/utils", StaticFiles(directory="utils"), name="utils")
        self.last_prices_collection = last_prices_collection
        self.save_to_file = save_to_file
        self.tokens_analyzer = tokens_analyzer

        # Setup routes
        self._setup_routes()

    def _setup_routes(self):
        """Setup all web routes."""

        @self.app.get("/", response_class=HTMLResponse)
        async def root(request: Request):
            """Main page with system status."""
            return await self._render_main_page(request)

        @self.app.get("/api/status")
        async def get_status():
            """API endpoint to get system status."""
            return {
                "status": "running",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "message": "Token analyzer is running and logging data every 10 seconds",
            }

        @self.app.get("/api/data")
        async def get_tokens_data():
            """API endpoint to get tokens analyzer data."""
            return await self._load_tokens_data()

        @self.app.get("/api/test")
        async def test_api():
            """Test API endpoint."""
            return {"status": "success", "message": "API is working"}

        @self.app.post("/api/update-filters")
        async def update_filters(request: FilterUpdate):
            """API endpoint to update token analyzer filters."""
            try:
                periods = request.periods
                thresholds = request.thresholds

                if self.tokens_analyzer:
                    # Update periods
                    if periods:
                        self.tokens_analyzer.periods.update(periods)
                        self.logger.info(f"📊 FILTER UPDATE - Periods: {periods}")

                    # Update thresholds
                    if thresholds:
                        self.tokens_analyzer.thresholds.update(thresholds)
                        self.logger.info(f"📊 FILTER UPDATE - Thresholds: {thresholds}")

                    return {
                        "status": "success",
                        "message": "Filters updated successfully",
                    }
                else:
                    return {
                        "status": "error",
                        "message": "Token analyzer not available",
                    }

            except Exception as e:
                self.logger.error(f"Error updating filters: {e}")
                return {"status": "error", "message": str(e)}

        @self.app.get("/api/symbols")
        async def get_symbols():
            """API endpoint to get symbols from config.json."""
            try:
                if self.settings.symbols_spot and self.settings.symbols:
                    return {"status": "success", "data": self.settings.symbols}
                else:
                    return {"status": "error", "message": "No symbols available"}
            except Exception as e:
                self.logger.error(f"Error loading symbols: {e}")
                return {"status": "error", "message": str(e)}

        @self.app.post("/api/symbols")
        async def update_symbols(request: dict):
            """API endpoint to update symbols in config.json."""
            try:
                self.settings.symbols_spot = request.get("symbols_spot", [])
                self.settings.symbols = request.get("symbols", [])
            except Exception as e:
                self.logger.error(f"Error updating symbols: {e}")
                return {"status": "error", "message": str(e)}
            self.logger.info(f"📊 SYMBOLS UPDATE - Updated {len(self.settings.symbols_spot)} symbols")
            return {"status": "success", "message": "Symbols updated successfully"}

        @self.app.get("/api/exchanges")
        async def get_exchanges():
            """API endpoint to get exchanges from config.json."""
            try:
                if self.settings.exchanges:
                    return {"status": "success", "data": self.settings.exchanges}
                else:
                    return {"status": "error", "message": "No exchanges available"}
            except Exception as e:
                self.logger.error(f"Error loading exchanges: {e}")
                return {"status": "error", "message": str(e)}

        @self.app.post("/api/exchanges")
        async def update_exchanges(request: dict):
            """API endpoint to update exchanges in config.json."""
            try:
                self.settings.exchanges = request.get("exchanges", [])
            except Exception as e:
                self.logger.error(f"Error updating exchanges: {e}")
                return {"status": "error", "message": str(e)}
            self.logger.info(f"📊 EXCHANGES UPDATE - Updated {len(self.settings.exchanges)} exchanges")
            return {"status": "success", "message": "Exchanges updated successfully"}

        @self.app.get("/api/orders")
        async def get_orders():
            """API endpoint to get orders from orders.json."""
            try:
                orders_path = "utils/orders.json"
                if os.path.exists(orders_path):
                    with open(orders_path, encoding="utf-8") as f:
                        orders = json.load(f)
                        return {"status": "success", "data": orders}
                else:
                    return {"status": "error", "message": "Orders file not found"}
            except Exception as e:
                self.logger.error(f"Error loading orders: {e}")
                return {"status": "error", "message": str(e)}

        @self.app.post("/api/orders")
        async def update_orders(request: dict):
            """API endpoint to update orders in orders.json."""
            try:
                orders_path = "utils/orders.json"
                orders = request.get("orders", [])

                with open(orders_path, "w", encoding="utf-8") as f:
                    json.dump(orders, f, indent=2, ensure_ascii=False)

                self.logger.info(f"📊 ORDERS UPDATE - Updated {len(orders)} orders")
                return {"status": "success", "message": "Orders updated successfully"}
            except Exception as e:
                self.logger.error(f"Error updating orders: {e}")
                return {"status": "error", "message": str(e)}

    async def _load_tokens_data(self):
        """Load tokens analyzer data from analyzer or file."""
        try:
            data_path = self.settings.tokens_output_path
            file_data = {}
            analyzer_data = {}
            
            # Try to get real-time data from tokens analyzer if available
            if self.tokens_analyzer:
                try:
                    analyzer_data = self.tokens_analyzer.filter_and_save()
                    if analyzer_data and len(analyzer_data) > 0:
                        self.logger.debug(f"Loaded real-time data from analyzer: {len(analyzer_data)} exchanges")
                except Exception as e:
                    self.logger.debug(f"Analyzer data not available: {e}")
            
            # Also read from file for persistence
            if os.path.exists(data_path):
                try:
                    with open(data_path, encoding="utf-8") as f:
                        file_data = json.load(f)
                    if file_data and len(file_data) > 0:
                        self.logger.debug(f"Loaded data from file: {len(file_data)} exchanges")
                except Exception as e:
                    self.logger.debug(f"File data not available: {e}")
            
            # Merge data: prefer analyzer data (real-time), fallback to file data
            merged_data = {}
            
            # Add all exchanges from analyzer (real-time, higher priority)
            for exchange, tokens in analyzer_data.items():
                if not exchange.startswith('_'):
                    merged_data[exchange] = tokens
            
            # Add exchanges from file that aren't in analyzer
            for exchange, tokens in file_data.items():
                if not exchange.startswith('_') and exchange not in merged_data:
                    merged_data[exchange] = tokens
            
            # Add timestamp for cache busting
            result = {
                **merged_data,
                "_timestamp": datetime.now().isoformat(),
                "_source": "analyzer" if analyzer_data else "file"
            }
            
            return result

        except Exception as e:
            self.logger.error(f"Error loading tokens data: {e}")
            return {"_timestamp": datetime.now().isoformat(), "_error": str(e)}

    async def _render_main_page(self, request: Request) -> HTMLResponse:
        """Render the main page with status information."""
        try:
            context = {
                "request": request,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            response = self.templates.TemplateResponse("index.html", context)
            return HTMLResponse(
                content=(response.body.decode("utf-8") if isinstance(response.body, bytes) else response.body),
                status_code=200,
            )

        except Exception as e:
            self.logger.error(f"Error rendering main page: {e}")
            # Return simple error page
            error_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Crypto Arbitrage Analyzer - Error</title>
                <meta charset="utf-8">
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 40px; }}
                    .error {{ color: red; }}
                </style>
            </head>
            <body>
                <h1>Crypto Arbitrage Analyzer</h1>
                <div class="error">
                    <h2>Error loading page</h2>
                    <p>{str(e)}</p>
                </div>
            </body>
            </html>
            """
            return HTMLResponse(content=error_html, status_code=500)

    async def start(self):
        """Start the web server."""
        self.logger.info(f"Starting web server on {self.host}:{self.port}")
        config = uvicorn.Config(self.app, host=self.host, port=self.port, log_level="info")
        server = uvicorn.Server(config)
        await server.serve()

    def run(self):
        """Run the web server (blocking)."""
        asyncio.run(self.start())


# Create templates directory
def create_templates():
    """Create templates directory."""
    os.makedirs("templates", exist_ok=True)


if __name__ == "__main__":
    # Create templates directory and files
    create_templates()

    # Start web server
    server = WebServer()
    server.run()
