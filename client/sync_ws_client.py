from websockets.sync.client import connect
from threading import Thread


def listener(ws, my_name) -> None:
    while True:
        recv_message = ws.recv().decode()
        if not recv_message.startswith(f'{my_name}:'):
            print(recv_message)


def writer(ws) -> None:
    while True:
        msg = input()
        ws.send(msg.encode())


def main():
    uri = "wss://3317-93-109-70-44.ngrok-free.app"
    
    with connect(uri) as websocket:
        name = input("Enter your name: ")
        websocket.send(f"name:{name}".encode())
        thread_listener = Thread(target=listener, args=(websocket, name), daemon=True)
        thread_listener.start()
        
        writer(websocket)


main()
