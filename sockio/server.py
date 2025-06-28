from socketify import (
    App,
    CompressOptions,
    WebSocket,
)

from sockio.log import make_logger

logger = make_logger('main')

clients = {}
ROOM_NAME = 'room'


def on_connect(ws: WebSocket):
    logger.debug("A WebSocket got connected!")
    ws.subscribe(ROOM_NAME)
    return 1


def answer_greeting(ws: WebSocket, message: bytes) -> None:
    if message.startswith(b'name:'):
        new_client_name = message.split(b':')[1].decode()
        ws.send(f'Server: Hello, {new_client_name}!'.encode())


def on_message(ws: WebSocket, message: bytes, _: int):
    logger.debug(f'Received message: {message}')
    answer_greeting(message=message, ws=ws)
    ws.publish(ROOM_NAME, message=message)
    return 1


def main() -> None:
    app = App()
    app.ws(
        "/*",
        {
            "compression": CompressOptions.SHARED_COMPRESSOR,
            "max_payload_length": 1024 * 1024 * 1024,
            "idle_timeout": 900,
            "open": on_connect,
            "message": on_message,
            "drain": lambda ws: print(
                "WebSocket backpressure: %s", ws.get_buffered_amount()
            ),
            "close": lambda ws, code, message: logger.debug("WebSocket closed"),
        },
    )
    app.any("/", lambda res, req: res.end("Nothing to see here!'"))
    app.listen(
        3000,
        lambda config: logger.debug("Listening on port http://localhost:%d now\n" % (config.port)),
    )
    app.run()


main()
