import logging
from collections.abc import Iterator
from websockets.sync.client import connect, ClientConnection
from threading import Thread

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

URI = "ws://orro.chat"
IMAGE_COMMAND = '/send_image'
LIST_OF_IMAGES_COMMAND = '/list_images'
BATCH_SIZE = 4096
SPLITTER = b':::'
SPLITTER_STR = SPLITTER.decode()
IMAGES_TO_SAVE: dict[bytes, list[bytes]] = {}


def format_start_message(image_name: str) -> bytes:
    return f"start_image{SPLITTER_STR}{image_name}".encode()


def format_batch_message(image_name: str, batch_number: int) -> bytes:
    return f"batch_image{SPLITTER_STR}{image_name}{SPLITTER_STR}{batch_number}{SPLITTER_STR}".encode()


def format_end_message(image_name: str) -> bytes:
    return f"end_image{SPLITTER_STR}{image_name}".encode()


def listener(client_conn: ClientConnection) -> None:
    while True:
        recv_message: bytes = client_conn.recv()

        if recv_message.startswith(f'start_image{SPLITTER_STR}'.encode()):
            parts = recv_message.split(SPLITTER, 1)
            image_name = parts[1]
            IMAGES_TO_SAVE[image_name] = []

        elif recv_message.startswith(f'image_list{SPLITTER_STR}'.encode()):
            logger.info(IMAGES_TO_SAVE)
            parts = recv_message.split(SPLITTER) #1



        elif recv_message.startswith(f'batch_image{SPLITTER_STR}'.encode()):
            parts = recv_message.split(SPLITTER, 3)
            if len(parts) < 4:
                logger.error(f"Malformed batch_image message: {recv_message}")
                continue

            name = parts[1]
            batch_number = int(parts[2])
            data = parts[3]
            IMAGES_TO_SAVE[name].insert(batch_number, data)

        elif recv_message.startswith(f'end_image{SPLITTER_STR}'.encode()):
            parts = recv_message.split(SPLITTER, 1)
            name = parts[1]
            image_data = b''.join(IMAGES_TO_SAVE[name])
            file_name = 'copy_' + name.decode(errors='replace')
            write_image(name=file_name, data=image_data)
            logger.info(f"Image '{file_name}' received and saved.")

        else:
            logger.info(f'RECV message: {recv_message}')


def start_writer(client_conn: ClientConnection) -> None:
    while True:
        msg = input()
        if msg.startswith(IMAGE_COMMAND):
            name_of_file: str = msg.split(' ', 1)[-1]
            my_image_data: Iterator[bytes] = read_image(name_of_file)

            client_conn.send(format_start_message(name_of_file))

            for i, batch in enumerate(my_image_data):
                header = format_batch_message(name_of_file, i)
                client_conn.send(header + batch)

            client_conn.send(format_end_message(name_of_file))
        elif msg.startswith(LIST_OF_IMAGES_COMMAND):
            client_conn.send(f'image_list{SPLITTER_STR}'.encode())

        else:
            client_conn.send(msg.encode())


def start_listener(client_conn: ClientConnection) -> None:
    thread_listener = Thread(target=listener, args=(client_conn,), daemon=True)
    thread_listener.start()


def send_greeting(client_conn: ClientConnection, my_name: str) -> None:
    client_conn.send(f"name:{my_name}".encode())


def read_image(name: str) -> Iterator[bytes]:
    with open(name, "rb") as image_file:
        while True:
            chunk = image_file.read(BATCH_SIZE)
            if not chunk:
                break
            yield chunk


def write_image(name: str, data: bytes) -> None:
    with open(name, "wb") as image_file:
        image_file.write(data)


def main() -> None:
    with connect(URI) as client_conn:
        start_listener(client_conn)
        start_writer(client_conn)


if __name__ == '__main__':
    main()
