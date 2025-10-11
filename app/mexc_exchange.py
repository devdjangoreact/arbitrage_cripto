import asyncio
import hashlib
import json
import time
from datetime import datetime
from typing import Dict, List, Optional

import aiohttp

from utils.logger import get_logger
from utils.settings import get_settings


class MEXCExchange:
    """
    MEXC Exchange implementation for futures trading.
    Supports creating, modifying, canceling orders and fetching market data.
    """

    def __init__(self, api_key: str = None, logger=None):
        """
        Initialize MEXC exchange.

        Args:
            api_key: MEXC API key
            logger: Logger instance
        """
        self.api_key = api_key or get_settings().mexc_id
        self.logger = logger or get_logger()

        # MEXC API endpoints
        self.base_url = "https://futures.mexc.com/api/v1"
        self.contract_url = "https://contract.mexc.com/api/v1"

        # Headers for authenticated requests
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
        }

        if self.api_key:
            self.headers["Authorization"] = self.api_key

        # Session management
        self._session = None
        self._timeout = aiohttp.ClientTimeout(total=30, connect=10)

    async def _get_session(self):
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=self._timeout)
        return self._session

    def _md5_hash(self, value: str) -> str:
        """Generate MD5 hash of input string."""
        return hashlib.md5(value.encode("utf-8")).hexdigest()

    def _generate_signature(self, obj: Dict = None) -> Dict[str, str]:
        """
        Generate MEXC signature for authenticated requests.

        Args:
            obj: Request body object

        Returns:
            Dict with timestamp and signature
        """
        if not self.api_key:
            raise ValueError("API key is required for authenticated requests")

        date_now = str(int(time.time() * 1000))
        g = self._md5_hash(self.api_key + date_now)[7:]
        s = json.dumps(obj or {}, separators=(",", ":"))
        sign = self._md5_hash(date_now + s + g)
        return {"time": date_now, "sign": sign}

    async def _make_request(
        self, method: str, url: str, data: Dict = None, authenticated: bool = False
    ) -> Dict:
        """
        Make HTTP request to MEXC API.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: Full URL
            data: Request data
            authenticated: Whether to include authentication headers

        Returns:
            Response data as dict
        """
        headers = self.headers.copy()

        if authenticated and self.api_key:
            signature = self._generate_signature(data)
            headers["x-mxc-sign"] = signature["sign"]
            headers["x-mxc-nonce"] = signature["time"]

        # Get or create session
        session = await self._get_session()
        try:
            if method.upper() == "GET":
                async with session.get(url, headers=headers) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        self.logger.error(f"HTTP error {response.status}: {error_text}")
                        return {"error": f"HTTP {response.status}", "data": error_text}

                    try:
                        result = await response.json()
                    except aiohttp.ContentTypeError:
                        error_text = await response.text()
                        self.logger.error(f"Invalid JSON response: {error_text}")
                        return {"error": "Invalid JSON response", "data": error_text}
            elif method.upper() == "POST":
                async with session.post(url, headers=headers, json=data) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        self.logger.error(f"HTTP error {response.status}: {error_text}")
                        return {"error": f"HTTP {response.status}", "data": error_text}

                    try:
                        result = await response.json()
                    except aiohttp.ContentTypeError:
                        error_text = await response.text()
                        self.logger.error(f"Invalid JSON response: {error_text}")
                        return {"error": "Invalid JSON response", "data": error_text}
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            return result

        except asyncio.TimeoutError:
            self.logger.error(f"Request timeout for {url}")
            return {"error": "Request timeout"}
        except aiohttp.ClientError as e:
            self.logger.error(f"Client error: {e}")
            return {"error": f"Client error: {str(e)}"}
        except Exception as e:
            self.logger.error(f"Request failed: {e}")
            return {"error": str(e)}

    async def get_futures_price(self, symbol: str) -> Optional[float]:
        """
        Get current futures price for a symbol.

        Args:
            symbol: Trading symbol (e.g., 'BTC_USDT')

        Returns:
            Current price or None if error
        """
        url = f"{self.contract_url}/contract/ticker"
        params = {"symbol": symbol}

        # Add params to URL
        param_str = "&".join([f"{k}={v}" for k, v in params.items()])
        full_url = f"{url}?{param_str}"

        result = await self._make_request("GET", full_url)

        if "error" in result:
            self.logger.error(f"Failed to get price for {symbol}: {result['error']}")
            return None

        if "data" in result and "lastPrice" in result["data"]:
            return float(result["data"]["lastPrice"])

        self.logger.error(f"Invalid response format for {symbol}: {result}")
        return None

    async def get_contract_details(self) -> Dict:
        """
        Get contract details for all symbols.

        Returns:
            Contract details data
        """
        url = f"{self.base_url}/contract/detailV2?client=web"
        return await self._make_request("GET", url)

    async def compute_volume(
        self, symbol: str, usdt_size: float, price: float, leverage: int = 1
    ) -> int:
        """
        Compute volume for a given USDT size.

        Args:
            symbol: Trading symbol
            usdt_size: USDT amount to trade
            price: Current price
            leverage: Leverage multiplier

        Returns:
            Computed volume
        """
        try:
            contract_details = await self.get_contract_details()
            if "data" in contract_details:
                for contract in contract_details["data"]:
                    if contract["symbol"] == symbol:
                        cs = contract["cs"]  # Contract size
                        return round(usdt_size * leverage / (cs * price))
            return 0
        except Exception as e:
            self.logger.error(f"Error computing volume: {e}")
            return 0

    async def create_order(
        self,
        symbol: str,
        side: int,
        open_type: int,
        order_type: str,
        vol: float,
        leverage: int = 20,
        price: str = None,
        price_protect: str = "0",
    ) -> Dict:
        """
        Create a futures order on MEXC.

        Args:
            symbol: Trading symbol
            side: Order side (1=open long, 2=open short, 3=close short, 4=close long)
            open_type: Open type (1=isolated, 2=cross)
            order_type: Order type ("1"=limit, "2"=market)
            vol: Order volume
            leverage: Leverage
            price: Order price (for limit orders)
            price_protect: Price protection

        Returns:
            Order creation result
        """
        if not self.api_key:
            return {"error": "API key required for order creation"}

        obj = {
            "symbol": symbol,
            "side": side,
            "openType": open_type,
            "type": order_type,
            "vol": vol,
            "leverage": leverage,
            "priceProtect": price_protect,
        }

        if price:
            obj["price"] = price

        url = f"{self.base_url}/private/order/create"
        result = await self._make_request("POST", url, obj, authenticated=True)

        if result.get("success"):
            self.logger.info(f"Order created successfully: {result}")
        else:
            self.logger.error(f"Order creation failed: {result}")

        return result

    async def get_open_orders(self, page_size: int = 200) -> Dict:
        """
        Get open orders.

        Args:
            page_size: Number of orders to fetch

        Returns:
            Open orders data
        """
        if not self.api_key:
            return {"error": "API key required for fetching orders"}

        url = f"{self.base_url}/private/order/list/open_orders?page_size={page_size}"
        return await self._make_request("GET", url, authenticated=True)

    async def chase_order(self, order_id: str) -> Dict:
        """
        Chase (modify) an existing order to best bid/ask.

        Args:
            order_id: Order ID to chase

        Returns:
            Chase result
        """
        if not self.api_key:
            return {"error": "API key required for chasing orders"}

        obj = {"orderId": order_id}
        url = f"{self.base_url}/private/order/chase_limit_order"
        return await self._make_request("POST", url, obj, authenticated=True)

    async def get_open_positions(self) -> Dict:
        """
        Get open positions.

        Returns:
            Open positions data
        """
        if not self.api_key:
            return {"error": "API key required for fetching positions"}

        url = f"{self.base_url}/private/position/open_positions"
        return await self._make_request("GET", url, authenticated=True)

    async def cancel_order(self, order_id: str, symbol: str) -> Dict:
        """
        Cancel an order.

        Args:
            order_id: Order ID to cancel
            symbol: Trading symbol

        Returns:
            Cancel result
        """
        if not self.api_key:
            return {"error": "API key required for canceling orders"}

        obj = {"orderId": order_id, "symbol": symbol}
        url = f"{self.base_url}/private/order/cancel"
        return await self._make_request("POST", url, obj, authenticated=True)

    async def get_order_book(self, symbol: str) -> Dict:
        """
        Get order book for a symbol.

        Args:
            symbol: Trading symbol

        Returns:
            Order book data
        """
        url = f"{self.contract_url}/contract/depth"
        params = {"symbol": symbol}

        param_str = "&".join([f"{k}={v}" for k, v in params.items()])
        full_url = f"{url}?{param_str}"

        return await self._make_request("GET", full_url)

    async def get_ticker(self, symbol: str) -> Dict:
        """
        Get ticker data for a symbol.

        Args:
            symbol: Trading symbol

        Returns:
            Ticker data
        """
        url = f"{self.contract_url}/contract/ticker"
        params = {"symbol": symbol}

        param_str = "&".join([f"{k}={v}" for k, v in params.items()])
        full_url = f"{url}?{param_str}"

        return await self._make_request("GET", full_url)

    # CCXT-compatible methods for integration with exchanges_ws.py
    async def watch_order_book(self, symbol: str) -> Dict:
        """
        Watch order book (CCXT-compatible method).

        Args:
            symbol: Trading symbol

        Returns:
            Order book data in CCXT format
        """
        try:
            # Get order book data
            order_book = await self.get_order_book(symbol)

            if "error" in order_book:
                raise Exception(f"Failed to get order book: {order_book['error']}")

            # Convert to CCXT format
            data = order_book.get("data", {})
            asks = [[float(ask[0]), float(ask[1])] for ask in data.get("asks", [])]
            bids = [[float(bid[0]), float(bid[1])] for bid in data.get("bids", [])]

            return {
                "symbol": symbol,
                "asks": asks,
                "bids": bids,
                "timestamp": int(time.time() * 1000),
                "datetime": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            self.logger.error(f"Error watching order book for {symbol}: {e}")
            raise

    async def create_order_ccxt(
        self,
        symbol: str,
        side: str,
        amount: float,
        price: float = None,
        order_type: str = "market",
        **kwargs,
    ) -> Dict:
        """
        Create order (CCXT-compatible method).

        Args:
            symbol: Trading symbol
            side: Order side ('buy' or 'sell')
            amount: Order amount in USDT
            price: Order price
            order_type: Order type
            **kwargs: Additional parameters

        Returns:
            Order creation result in CCXT format
        """
        try:
            # Convert CCXT parameters to MEXC format
            mexc_side = 1 if side == "buy" else 2  # Default to open long/short
            mexc_order_type = "1" if order_type == "limit" else "2"
            open_type = kwargs.get("openType", 1)  # 1=isolated, 2=cross
            leverage = kwargs.get("leverage", 20)

            # Handle position closing
            if kwargs.get("close_position", False):
                mexc_side = 4 if side == "buy" else 3  # Close long/short

            # Convert USDT amount to contract volume
            if price is None and order_type == "market":
                # For market orders, get current price
                current_price = await self.get_futures_price(symbol)
                if current_price is None:
                    raise Exception(f"Failed to get current price for {symbol}")
                price = current_price

            # Convert USDT amount to contract volume
            vol = await self.compute_volume(symbol, amount, price, leverage)
            if vol <= 0:
                raise Exception(
                    f"Invalid volume calculated: {vol} for amount {amount} USDT"
                )

            result = await self.create_order(
                symbol=symbol,
                side=mexc_side,
                open_type=open_type,
                order_type=mexc_order_type,
                vol=vol,
                leverage=leverage,
                price=str(price) if price else None,
            )

            if result.get("success"):
                # Convert to CCXT format
                order_data = result.get("data", {})
                return {
                    "id": order_data.get("orderId"),
                    "symbol": symbol,
                    "side": side,
                    "amount": amount,
                    "price": price,
                    "type": order_type,
                    "status": "open",
                    "filled": 0,
                    "remaining": amount,
                    "info": result,
                }
            else:
                raise Exception(f"Order creation failed: {result}")

        except Exception as e:
            self.logger.error(f"Error creating order: {e}")
            raise

    async def cancel_order_ccxt(self, order_id: str, symbol: str) -> Dict:
        """
        Cancel order (CCXT-compatible method).

        Args:
            order_id: Order ID to cancel
            symbol: Trading symbol

        Returns:
            Cancel result
        """
        return await self.cancel_order(order_id, symbol)

    async def fetch_open_orders(self, symbol: str = None) -> List[Dict]:
        """
        Fetch open orders (CCXT-compatible method).

        Args:
            symbol: Optional symbol filter

        Returns:
            List of open orders
        """
        result = await self.get_open_orders()

        if "error" in result:
            raise Exception(f"Failed to fetch orders: {result['error']}")

        orders = result.get("data", [])

        if symbol:
            # Filter by symbol if provided
            orders = [order for order in orders if order.get("symbol") == symbol]

        # Convert to CCXT format
        ccxt_orders = []
        for order in orders:
            ccxt_orders.append(
                {
                    "id": order.get("orderId"),
                    "symbol": order.get("symbol"),
                    "side": "buy" if order.get("side") in [1, 3] else "sell",
                    "amount": order.get("vol"),
                    "price": order.get("price"),
                    "type": "limit" if order.get("type") == "1" else "market",
                    "status": "open",
                    "filled": order.get("filled", 0),
                    "remaining": order.get("remaining", order.get("vol")),
                    "info": order,
                }
            )

        return ccxt_orders

    async def close(self):
        """Close the exchange connection."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    @property
    def id(self) -> str:
        """Exchange ID for compatibility."""
        return "mexc"


async def test_class_mexc_exchange():
    """Simple test for MEXC exchange operations."""
    mexc = MEXCExchange()

    # Get price
    price = await mexc.get_futures_price("BTC_USDT")
    print(f"BTC price: {price}")

    # Test volume computation
    usdt_amount = 100  # 100 USDT
    vol = await mexc.compute_volume("BTC_USDT", usdt_amount, price, 20)
    print(f"Volume for {usdt_amount} USDT at {price}: {vol}")

    # Create limit order using CCXT method (USDT amount)
    order = await mexc.create_order_ccxt(
        symbol="BTC_USDT",
        side="buy",  # Open long
        amount=20,  # 20 USDT
        price=price * 0.8,  # Half current price
        order_type="limit",
        leverage=5,
    )
    print(f"CCXT Order: {order}")

    # Create market order using CCXT method (USDT amount)
    market_order = await mexc.create_order_ccxt(
        symbol="BTC_USDT",
        side="sell",  # Open short
        amount=25,  # 25 USDT
        order_type="market",
        leverage=20,
    )
    print(f"CCXT Market order: {market_order}")

    # Close long using CCXT method
    close_order = await mexc.create_order_ccxt(
        symbol="BTC_USDT",
        side="sell",  # Close long
        amount=50,  # 50 USDT
        price=price * 1.001,
        order_type="limit",
        leverage=20,
        close_position=True,
    )
    print(f"CCXT Close order: {close_order}")

    await mexc.close()


if __name__ == "__main__":
    print("Starting MEXC exchange test...")
    # Uncomment the line below to run the test
    import asyncio

    asyncio.run(test_class_mexc_exchange())
