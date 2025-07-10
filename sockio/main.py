from socketify import ASGI, AppOptions, CompressOptions, WebSocket

from sockio.config import config
from sockio.connection_manager import connection_manager
from sockio.db import create_default_admin_user, init_db
from sockio.fastapi_app import app as fastapi_app
from sockio.log import make_logger
from sockio.message_handler import message_handler

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
    logger.warning(
        f"WebSocket backpressure: {ws.get_buffered_amount()}",
        connection_id=connection_id,
    )


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
        # await periodic_cleanup()
        config.ensure_upload_dir()
        logger.info("Server setup completed successfully")
    except Exception as e:
        logger.error(f"Failed to setup server: {e}")
        raise


def create_server() -> ASGI:
    fastapi_app.add_event_handler("startup", setup_server)

    server = ASGI(
        fastapi_app,
        options=AppOptions(
            key_file_name=config.pem_key_path,
            cert_file_name=config.pem_chain_path,
        ),
        websocket={
            "compression": CompressOptions.SHARED_COMPRESSOR,
            "max_payload_length": config.ws_max_payload,
            "idle_timeout": config.ws_idle_timeout,
            "open": on_connect,
            "message": on_message,
            "drain": on_drain,
            "close": on_close,
        },
        websocket_options=None,
        lifespan=True,
    )

    return server


if __name__ == "__main__":
    server = create_server()
    logger.info(
        f"Starting server on {config.ws_host}:{config.ws_port}, WebSocket endpoint: {config.ws_url}/ws"
    )
    server.listen(
        config.ws_port, lambda _: logger.info(f"Server listening on {config.ws_url}")
    )
    server.run()
