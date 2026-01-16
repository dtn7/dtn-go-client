import logging
from socket import AF_UNIX, SOCK_STREAM, socket

from dtnclient.messages import *


class DataError(Exception):
    """Data received from dtnd is inconsistent"""


class DTNDError(Exception):
    """dtnd's response indicated an error"""


def send_message(socket_path: str, message: Message) -> Response:
    """

    Args:
        socket_path: Path to dtnd's UNIX-application-agent-socket
        message: Message to be sent

    Returns:
        dtnd's response to the message

    Raises:
        FileNotFoundError: if socket_path does not resolve
        DataError: if data received from dtnd is inconsistent
        DTNDError: if dtnd's response indicated an error
    """

    with socket(AF_UNIX, SOCK_STREAM) as s:
        s.connect(socket_path)

        logging.debug(f"Sending message: {message}")

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

        if reply_length <= 0:
            raise DataError(f"Received nonsensical data-length: {reply_length}")

        data = s.recv(reply_length)
        if len(data) != reply_length:
            raise DataError(
                f"Announced data length and actual length do not match - announced: {reply_length}, actual: {len(data)}"
            )

        reply = deserialize(serialized=data)
        logging.debug(f"Received reply: {reply}")

        if not isinstance(reply, Response):
            raise DataError(
                f"Received response is not a response message - message type: {type(reply)}"
            )

        return reply


def register_unregister(socket_path: str, eid: EID, register: bool = True) -> None:
    """
    Performs (un)registration of an EndpointID

    Args:
        socket_path: Path to dtnd's UNIX-application-agent-socket
        eid: EndpointID to be (un)registered
        register: True if we want to register the EID, False if we want to unregister

    Raises:
        FileNotFoundError: if socket_path does not resolve
        DataError: if data received from dtnd is inconsistent
        DTNDError: if dtnd's response indicated an error
    """

    operation: MessageType
    if register:
        logging.info("Performing registration")
        operation = MessageType.RegisterEID
    else:
        logging.info("Performing unregistration")
        operation = MessageType.UnregisterEID

    message = RegisterUnregister(Type=operation, EndpointID=eid)

    response = send_message(socket_path=socket_path, message=message)

    if response.Error:
        raise DTNDError(response.Error)

    if register:
        logging.info("Successfully registered with dtnd")
    else:
        logging.info("Successfully unregistered with dtnd")
