import asyncio
from socketify import App, CompressOptions, WebSocket, AppOptions
from sockio.log import make_logger
from sockio.config import config
from sockio.db import init_db, create_default_admin_user
from sockio.connection_manager import connection_manager
from sockio.message_handler import message_handler
from sockio.api import SocketifyAPI
from sockio.swagger_ui import SwaggerHandler

logger = make_logger("main")


async def on_connect(ws: WebSocket):
    try:
        connection_id = await connection_manager.add_connection(ws)
        ws.connection_id = connection_id
        logger.debug("WebSocket connection established")
        return 1
    except Exception as e:
        logger.error(f"Error in on_connect: {e}")
        return 0


async def on_message(ws: WebSocket, message: bytes, _: int):
    try:
        connection_id = getattr(ws, "connection_id", None)
        if not connection_id:
            logger.error("WebSocket missing connection ID")
            return 0
        
        await message_handler.handle_message(connection_id, message)
        return 1
    except Exception as e:
        logger.error(f"Error in on_message: {e}")
        return 0


def on_drain(ws: WebSocket):
    connection_id = getattr(ws, "connection_id", None)
    logger.warning(f"WebSocket backpressure: {ws.get_buffered_amount()}",
                   connection_id=connection_id)


async def on_close(ws: WebSocket, code: int, message: bytes):
    try:
        connection_id = getattr(ws, "connection_id", None)
        if connection_id:
            await connection_manager.remove_connection(connection_id, code)
        logger.debug(f"WebSocket closed with code: {code}")
    except Exception as e:
        logger.error(f"Error in on_close: {e}")


async def setup_server():
    try:
        logger.info("Initializing database...")
        await init_db()
        await create_default_admin_user()
        #await periodic_cleanup()
        config.ensure_upload_dir()
        logger.info("Server setup completed successfully")
    except Exception as e:
        logger.error(f"Failed to setup server: {e}")
        raise


def create_app() -> App:
    app = App(
        AppOptions(
            key_file_name=config.pem_key_path,
            cert_file_name=config.pem_chain_path
        )
    )
    
    app.ws("/ws", {
        "compression": CompressOptions.SHARED_COMPRESSOR,
        "max_payload_length": config.ws_max_payload,
        "idle_timeout": config.ws_idle_timeout,
        "open": on_connect,
        "message": on_message,
        "drain": on_drain,
        "close": on_close,
    })
    
    SocketifyAPI(app)
    SwaggerHandler(app)
    app.on_start(setup_server)
    
    app.options("/*", lambda res, req: (
        res.write_header("Access-Control-Allow-Origin", "*"),
        res.write_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS"),
        res.write_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Session-Token"),
        res.write_header("Access-Control-Allow-Credentials", "true"),
        res.end("")
    ))
    
    return app


if __name__ == "__main__":
    app = create_app()
    logger.info(f"Starting unified server on {config.ws_host}:{config.ws_port}")
    logger.info(f"WebSocket endpoint: {config.ws_url}/ws")
    logger.info(f"HTTP API endpoints: {config.http_url}/api/*")
    logger.info(f"API Documentation: {config.http_url}/docs")
    logger.info(f"ReDoc Documentation: {config.http_url}/redoc")
    logger.info(f"WebSocket Documentation: {config.http_url}/websocket-docs")
    logger.info(f"OpenAPI Spec: {config.http_url}/api/openapi.json")
    app.listen(
        config.ws_port,
        lambda config_obj: logger.info(f"Server listening on {config.ws_url}")
    )
    app.run()


