from websockets.sync.client import connect
from threading import Thread
from time import sleep


def listener(ws) -> None:
    while True:
        sleep(0.01)
        print("\nReceived from server:", ws.recv())


def writer(ws) -> None:
    sleep(1)
    while True:
        ws.send(input('Enter msg:'))


def main():
    uri = "<YOUR URI>"
    
    with connect(uri) as websocket:
        thread_listener = Thread(target=listener, args=(websocket,))
        thread_listener.start()
        
        writer(websocket)


main()
