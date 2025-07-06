import asyncio


from socketify import App, CompressOptions, WebSocket

from sockio.log import make_logger
from sockio.config import config
from sockio.db import init_db

logger = make_logger('main')


def on_connect(ws: WebSocket):
    """Handle new WebSocket connection."""
    logger.debug("A WebSocket got connected!")
    ws.subscribe(config.ws_room_name)
    return 1


def on_message(ws: WebSocket, message: bytes, _: int):
    """Handle incoming WebSocket message."""
    logger.debug(f'Received message: {message}')
    ws.publish(config.ws_room_name, message=message)
    return 1


def on_drain(ws: WebSocket):
    """Handle WebSocket backpressure."""
    logger.warning(f"WebSocket backpressure: {ws.get_buffered_amount()}")


def on_close(ws: WebSocket, code: int, message: bytes):
    """Handle WebSocket connection close."""
    logger.debug(f"WebSocket closed with code: {code}")


def main() -> None:
    """Main application entry point."""
    logger.info('Initializing db...')
    asyncio.run(init_db())
    try:
        app = App()
        app.ws(
            "/*",
            {
                "compression": CompressOptions.SHARED_COMPRESSOR,
                "max_payload_length": config.ws_max_payload,
                "idle_timeout": config.ws_idle_timeout,
                "open": on_connect,
                "message": on_message,
                "drain": on_drain,
                "close": on_close,
            },
        )
        
        app.any("/", lambda res, req: res.end("WebSocket server running!"))
        app.get("/health", lambda res, req: res.end("OK"))
        app.listen(
            config.ws_port,
            lambda config_obj: logger.info(f"Server listening on {config.ws_url}")
        )
        
        app.run()
    
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        raise


main()
