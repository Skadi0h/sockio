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
    uri = "wss://b451-87-228-161-218.ngrok-free.app"
    
    with connect(uri) as websocket:
        thread_listener = Thread(target=listener, args=(websocket,))
        thread_listener.start()
        
        thread_writer = Thread(target=writer, args=(websocket,))
        thread_writer.start()
        
        sleep(999999)


main()
