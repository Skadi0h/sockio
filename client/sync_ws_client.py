import logging

from websockets.sync.client import (
    connect,
    ClientConnection
)
from threading import Thread

logger = logging.getLogger(__name__)
URI = "ws://localhost:3000"
IMAGE_COMMAND = '/send_image'
IMAGE_PROTOCOL = 'image:{image_name}:'


def listener(client_conn: ClientConnection, my_name: str) -> None:
    while True:
        recv_message: bytes = client_conn.recv()
        
        if recv_message.startswith(b'image:'):
            
            parts = recv_message.split(b':')
            image_name: bytes = parts[1]
            data: bytes = parts[2]
            #logger.critical(f'IMAGE RECEIVED {image_name}')
            write_image(f'copy+{image_name.decode()}', data)
        else:
            logger.critical(f'RECV message: {recv_message}')


def start_writer(client_conn: ClientConnection) -> None:
    while True:
        msg = input()
        if msg.startswith(IMAGE_COMMAND):
            name_of_file: str = msg.split(' ')[-1]
            my_image_data: bytes = read_image(name_of_file)
            msg_to_send = IMAGE_PROTOCOL.format(
                image_name=name_of_file,
            ).encode() + my_image_data
            logger.critical(f'MESSAGE TO SEND: {msg_to_send} ')
            client_conn.send(
              msg_to_send
            )
        else:
            client_conn.send(msg.encode())


def start_listener(client_conn: ClientConnection, my_name: str) -> None:
    thread_listener = Thread(target=listener, args=(client_conn, my_name), daemon=True)
    thread_listener.start()


def send_greeting(
    client_conn: ClientConnection,
    my_name: str
) -> None:
    client_conn.send(f"name:{my_name}".encode())


def read_image(name: str) -> bytes:
    with open(name, "rb") as image_file:
        return image_file.read()


def write_image(name: str, data: bytes) -> None:
    with open(name, "wb") as image_file:
        image_file.write(data)


def main() -> None:
    with connect(URI) as client_conn:
        name = input("Enter your name: ")
        
        send_greeting(client_conn, name)
        start_listener(client_conn, name)
        start_writer(client_conn)


if __name__ == '__main__':
    main()
