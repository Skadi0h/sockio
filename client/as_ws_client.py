import asyncio
import contextvars

import websockets

ws_ctx = contextvars.ContextVar('ws_ctx', default=None)


def send_msg(_) -> None:
    loop = asyncio.get_running_loop()
    my_message = input('Enter msg: ')
    loop.create_task(
        ws_ctx.get('ws_ctx').send(my_message)
    )


async def test_ws():
    uri = "wss://b451-87-228-161-218.ngrok-free.app"
    loop = asyncio.get_running_loop()
    async with websockets.connect(uri) as websocket:
        ws_ctx.set(websocket)
        while True:
            task = loop.create_task(
                websocket.recv(),
            )
            task.add_done_callback(
                send_msg
            )
            print("RECIEVED", await task)

asyncio.run(test_ws())
