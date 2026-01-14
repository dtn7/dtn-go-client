#! /usr/bin/env python3

import argparse
import logging
from socket import AF_UNIX, SOCK_STREAM, socket

from dtnclient.messages import *


def send_message(socket_path: str, message: Message) -> Response:
    with socket(AF_UNIX, SOCK_STREAM) as s:
        s.connect(socket_path)

        ## serialize message
        message_bytes = serialize(message=message)
        message_length = len(message_bytes)
        logging.debug(f"Message length: {message_length}")
        message_length_bytes = message_length.to_bytes(
            length=8, byteorder="big", signed=False
        )

        # send message
        s.sendall(message_length_bytes)
        logging.debug("Sent message length")
        s.sendall(message_bytes)
        logging.debug("Sent message")

        # receive and deserialize reply
        data = s.recv(8)
        reply_length = int.from_bytes(bytes=data, byteorder="big", signed=False)
        logging.debug(f"Reply length: {reply_length}")

        assert reply_length > 0

        data = s.recv(reply_length)
        reply = deserialize(serialized=data)
        logging.debug(f"Received reply: {reply}")

        assert isinstance(reply, Response)
        return reply


def main() -> None:
    parser = argparse.ArgumentParser(description="Interact with dtnd")


if __name__ == "__main__":
    main()
