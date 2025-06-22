import asyncio
import sys

import websockets
async def ainput(string: str) -> str:
    await asyncio.get_event_loop().run_in_executor(
            None, lambda s=string: sys.stdout.write(s+' '))
    return await asyncio.get_event_loop().run_in_executor(
            None, sys.stdin.readline)

async def test_ws():
    uri = "wss://b451-87-228-161-218.ngrok-free.app"

    async with websockets.connect(uri) as websocket:
   
        while True:
            print(await websocket.recv())
            await websocket.send(
                await ainput('Enter msg: ')
            )


asyncio.run(test_ws())
