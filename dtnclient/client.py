import logging
from socket import AF_UNIX, SOCK_STREAM, socket

from dtnclient.messages import *


class DataError(Exception):
    """Data received from dtnd is inconsistent"""


class DTNDError(Exception):
    """dtnd's response indicated an error"""


def _send_message(socket_path: str, message: Message) -> Response:
    """
    Sends a message to dtnd and receives its response

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
        logging.debug("Performing registration")
        operation = MessageType.RegisterEID
    else:
        logging.debug("Performing unregistration")
        operation = MessageType.UnregisterEID

    message = RegisterUnregister(Type=operation, EndpointID=eid)

    response = _send_message(socket_path=socket_path, message=message)

    if response.Error:
        raise DTNDError(response.Error)

    if register:
        logging.debug("Successfully registered with dtnd")
    else:
        logging.debug("Successfully unregistered with dtnd")


def create_bundle(socket_path: str, args: dict[str, Any]) -> str:
    """
    Creates a new bundle

    Args:
        socket_path: Path to dtnd's UNIX-application-agent-socket
        args: Dictionary containing arguments for bundle creation (see: https://github.com/dtn7/dtn7-go/blob/main/pkg/bpv7/bundle_builder.go method `BuildFromMap` for argument names/meanings

    Returns:
        BundleID (as string) of the newly created bundle

    Raises:
        FileNotFoundError: if socket_path does not resolve
        DataError: if data received from dtnd is inconsistent
        DTNDError: if dtnd's response indicated an error
    """

    message = BundleCreate(Type=MessageType.BundleCreate, Args=args)

    response = _send_message(socket_path=socket_path, message=message)

    if response.Error:
        raise DTNDError(response.Error)
    if not isinstance(response, BundleCreateResponse):
        raise DataError(
            f"response should have been BundleCreateResponse, was {type(response)}"
        )

    return response.BundleID


def list_bundles(socket_path: str, mailbox: EID, new_only: bool = False) -> list[str]:
    """
    Lists all bundles stored in a mailbox

    Args:
        socket_path: Path to dtnd's UNIX-application-agent-socket
        mailbox: EndpointID of the mailbox that we want to check
        new_only: Whether we want to list all bundles, or only 'new' ones (a bundle is new if it hasn't been fetched before)

    Returns:
        List of bundle-IDs of stored bundles

    Raises:
        FileNotFoundError: if socket_path does not resolve
        DataError: if data received from dtnd is inconsistent
        DTNDError: if dtnd's response indicated an error
    """

    message = ListBundles(Type=MessageType.ListBundles, Mailbox=mailbox, New=new_only)

    response = _send_message(socket_path=socket_path, message=message)

    if response.Error:
        raise DTNDError(response.Error)
    if not isinstance(response, ListResponse):
        raise DataError(f"response should have been ListResponse, was {type(response)}")

    return response.Bundles


def fetch_bundle(
    socket_path: str, mailbox: EID, bundle_id: str, delete: bool = False
) -> BundleContent:
    """
    Fetch one specific bundle fy its ID

    Args:
        socket_path: Path to dtnd's UNIX-application-agent-socket
        mailbox: EndpointID of the mailbox that we want to fetch from
        bundle_id: String-representation of the bundle's ID
        delete: Whether the bundle should be deleted after fetching

    Returns:
        BundleContent-object representing the bundle

    Raises:
        FileNotFoundError: if socket_path does not resolve
        DataError: if data received from dtnd is inconsistent
        DTNDError: if dtnd's response indicated an error
    """

    message = FetchBundle(
        Type=MessageType.FetchBundle, Mailbox=mailbox, BundleID=bundle_id, Remove=delete
    )

    response = _send_message(socket_path=socket_path, message=message)

    if response.Error:
        raise DTNDError(response.Error)
    if not isinstance(response, FetchBundleResponse):
        raise DataError(
            f"response should have been FetchBundleResponse, was {type(response)}"
        )

    return response.BundleContent


def fetch_all_bundles(
    socket_path: str, mailbox: EID, new_only: bool = False, delete: bool = False
) -> list[BundleContent]:
    """
    Fetch one specific bundle fy its ID

    Args:
        socket_path: Path to dtnd's UNIX-application-agent-socket
        mailbox: EndpointID of the mailbox that we want to fetch from
        new_only: Whether we want to fetch all bundles, or only 'new' ones (a bundle is new if it hasn't been fetched before)
        delete: Whether the bundles should be deleted after fetching

    Returns:
        List of BundleContent-objects representing the bundles

    Raises:
        FileNotFoundError: if socket_path does not resolve
        DataError: if data received from dtnd is inconsistent
        DTNDError: if dtnd's response indicated an error
    """

    message = FetchAllBundles(
        Type=MessageType.FetchAllBundles, Mailbox=mailbox, New=new_only, Remove=delete
    )

    response = _send_message(socket_path=socket_path, message=message)

    if response.Error:
        raise DTNDError(response.Error)
    if not isinstance(response, FetchAllBundlesResponse):
        raise DataError(
            f"response should have been FetchAllBundlesResponse, was {type(response)}"
        )

    return response.Bundles
