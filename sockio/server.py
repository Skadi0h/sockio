from socketify import (
    App,
    OpCode,
    CompressOptions,
    WebSocket,
)

from sockio.log import make_logger

logger = make_logger('main')

clients = {}


def ws_open(ws: WebSocket):
    logger.debug("A WebSocket got connected!")
    ws.subscribe('room')
    return 1


def ws_message(ws: WebSocket, message: bytes, opcode):
    logger.debug(f'Received message: {message}')
    if message.startswith(b'name:'):
        new_client_name = message.split(b':')[1].decode()
        clients[ws.get_remote_address()] = new_client_name
        ws.send(f'Server: Hello, {new_client_name}!'.encode())
    else:
        ws.publish('room', message=f'{clients[ws.get_remote_address()]}: {message.decode()}'.encode())
    return 1


def main() -> None:
    app = App()
    app.ws(
        "/*",
        {
            "compression": CompressOptions.SHARED_COMPRESSOR,
            "max_payload_length": 16 * 1024 * 1024,
            "idle_timeout": 900,
            "open": ws_open,
            "message": ws_message,
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
