from socketify import (
    App,
    OpCode,
    CompressOptions
)

from sockio.log import make_logger

logger = make_logger('main')


def ws_open(ws):
    logger.debug("A WebSocket got connected!")
    ws.subscribe('room')
    ws.send('Vanya Connected')
    return 1


def ws_message(ws, message, opcode):
    logger.debug(f'Received message: {message}')
    # Ok is false if backpressure was built up, wait for drain
    ws.publish('room', message=message)
    return 1

def main() -> None:
    app = App()
    app.ws(
        "/*",
        {
            "compression": CompressOptions.SHARED_COMPRESSOR,
            "max_payload_length": 16 * 1024 * 1024,
            "idle_timeout": 300,
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
