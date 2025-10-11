import asyncio
import json
import os
from datetime import datetime

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
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

    async def _load_tokens_data(self):
        """Load tokens analyzer data from analyzer or file."""
        try:
            # First try to get data from tokens analyzer if available
            if self.tokens_analyzer:
                try:
                    result = self.tokens_analyzer.filter_and_save()
                    if result:
                        self.logger.info(f"Loaded real-time tokens data from analyzer with {len(result)} exchanges")
                        return result
                except Exception as e:
                    self.logger.warning(f"Error getting data from tokens analyzer: {e}")

            # Fallback to JSON file if available
            if self.save_to_file:
                data_path = "data/tokens_analyzer.json"
                if os.path.exists(data_path):
                    with open(data_path, encoding="utf-8") as f:
                        data = json.load(f)
                        self.logger.info(f"Loaded tokens data from file with {len(data)} exchanges")
                        return data

            return {}

        except Exception as e:
            self.logger.error(f"Error loading tokens data: {e}")
            return {}

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
