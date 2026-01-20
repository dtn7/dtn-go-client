from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import IntEnum
from typing import Any, override

from ormsgpack import packb, unpackb

from dtnclient.eid import EID


class InvalidMessageError(ValueError):
    """Raised when a message is malformed"""


class MessageType(IntEnum):
    Response = 1
    RegisterEID = 2
    UnregisterEID = 3
    BundleCreate = 4
    BundleCreateResponse = 5
    ListBundles = 6
    ListResponse = 7
    FetchBundle = 8
    FetchBundleResponse = 9
    FetchAllBundles = 10
    FetchAllBundlesResponse = 11


@dataclass(frozen=True)
class Message:
    Type: MessageType

    def dictify(self) -> dict:
        return self.__dict__

    @classmethod
    def from_dict(cls, data) -> Message:
        return cls(**data)


@dataclass(frozen=True)
class Response(Message):
    Error: str

    def __post_init__(self) -> None:
        if self.Type != MessageType.Response:
            raise InvalidMessageError(
                f"Message needs MessageType {MessageType.Response}, but has {self.Type}"
            )

    @override
    def dictify(self) -> dict:
        parent_dict = super().dictify()
        own_dict = self.__dict__
        return parent_dict | own_dict

    @classmethod
    def from_dict(cls, data) -> Response:
        return cls(**data)


@dataclass(frozen=True)
class RegisterUnregister(Message):
    EndpointID: EID

    def __post_init__(self) -> None:
        if (
            self.Type != MessageType.RegisterEID
            and self.Type != MessageType.UnregisterEID
        ):
            raise InvalidMessageError(
                f"Message needs MessageType {MessageType.RegisterEID} or {MessageType.UnregisterEID}, but has {self.Type}"
            )
        if not self.EndpointID:
            raise InvalidMessageError("EndpointID must not be none/empty")

    @override
    def dictify(self) -> dict:
        parent_dict = super().dictify()
        own_dict = self.__dict__
        return parent_dict | own_dict

    @classmethod
    def from_dict(cls, data) -> RegisterUnregister:
        return cls(**data)


@dataclass(frozen=True)
class BundleCreate(Message):
    Args: dict[str, Any]

    def __post_init__(self) -> None:
        if self.Type != MessageType.BundleCreate:
            raise InvalidMessageError(
                f"Message needs MessageType {MessageType.BundleCreate}, but has {self.Type}"
            )
        if not self.Args:
            raise InvalidMessageError("Args must not be empty")

    @override
    def dictify(self) -> dict:
        parent_dict = super().dictify()
        own_dict = self.__dict__
        return parent_dict | own_dict

    @classmethod
    def from_dict(cls, data) -> BundleCreate:
        return cls(**data)


@dataclass(frozen=True)
class BundleCreateResponse(Response):
    BundleID: str

    def __post_init__(self) -> None:
        if self.Type != MessageType.BundleCreateResponse:
            raise InvalidMessageError(
                f"Message needs MessageType {MessageType.BundleCreateResponse}, but has {self.Type}"
            )
        if not self.BundleID:
            raise InvalidMessageError("BundleID must not be empty")

    @override
    def dictify(self) -> dict:
        parent_dict = super().dictify()
        own_dict = self.__dict__
        return parent_dict | own_dict

    @classmethod
    def from_dict(cls, data) -> BundleCreateResponse:
        return cls(**data)


@dataclass(frozen=True)
class ListBundles(Message):
    Mailbox: EID
    New: bool

    def __post_init__(self) -> None:
        if self.Type != MessageType.ListBundles:
            raise InvalidMessageError(
                f"Message needs MessageType {MessageType.ListBundles}, but has {self.Type}"
            )
        if not self.Mailbox:
            raise InvalidMessageError("Mailbox must not be none/empty")

    @override
    def dictify(self) -> dict:
        parent_dict = super().dictify()
        own_dict = self.__dict__
        return parent_dict | own_dict

    @classmethod
    def from_dict(cls, data) -> ListBundles:
        data["Mailbox"] = EID(data["Mailbox"])
        return cls(**data)


@dataclass(frozen=True)
class ListResponse(Response):
    Bundles: list[str]

    def __post_init__(self) -> None:
        if self.Type != MessageType.ListResponse:
            raise InvalidMessageError(
                f"Message needs MessageType {MessageType.ListResponse}, but has {self.Type}"
            )

    @override
    def dictify(self) -> dict:
        parent_dict = super().dictify()
        own_dict = self.__dict__
        return parent_dict | own_dict

    @classmethod
    def from_dict(cls, data) -> ListResponse:
        return cls(**data)


@dataclass(frozen=True)
class FetchBundle(Message):
    Mailbox: EID
    BundleID: str
    Remove: bool

    def __post_init__(self) -> None:
        if self.Type != MessageType.FetchBundle:
            raise InvalidMessageError(
                f"Message needs MessageType {MessageType.FetchBundle}, but has {self.Type}"
            )
        if not self.Mailbox:
            raise InvalidMessageError("Mailbox must not be none/empty")
        if not self.BundleID:
            raise InvalidMessageError("BundleID must not be empty")

    @override
    def dictify(self) -> dict:
        parent_dict = super().dictify()
        own_dict = self.__dict__
        return parent_dict | own_dict

    @classmethod
    def from_dict(cls, data) -> FetchBundle:
        data["Mailbox"] = EID(data["Mailbox"])
        return cls(**data)


@dataclass(frozen=True)
class FetchBundleResponse(Response):
    BundleContent: BundleContent

    def __post_init__(self) -> None:
        if self.Type != MessageType.FetchBundleResponse:
            raise InvalidMessageError(
                f"Message needs MessageType {MessageType.FetchBundleResponse}, but has {self.Type}"
            )

    @override
    def dictify(self) -> dict:
        parent_dict = super().dictify()
        own_dict = {"BundleContent": self.BundleContent.dictify()}
        return parent_dict | own_dict

    @classmethod
    def from_dict(cls, data) -> FetchBundleResponse:
        data["BundleContent"] = BundleContent.from_dict(data["BundleContent"])
        return cls(**data)


@dataclass(frozen=True)
class FetchAllBundles(Message):
    Mailbox: EID
    New: bool
    Remove: bool

    def __post_init__(self) -> None:
        if self.Type != MessageType.FetchAllBundles:
            raise InvalidMessageError(
                f"Message needs MessageType {MessageType.FetchAllBundles}, but has {self.Type}"
            )
        if not self.Mailbox:
            raise InvalidMessageError("Mailbox must not be none/empty")

    @override
    def dictify(self) -> dict:
        parent_dict = super().dictify()
        own_dict = self.__dict__
        return parent_dict | own_dict

    @classmethod
    def from_dict(cls, data) -> FetchAllBundles:
        data["Mailbox"] = EID(data["Mailbox"])
        return cls(**data)


@dataclass(frozen=True)
class FetchAllBundlesResponse(Response):
    Bundles: list[BundleContent]

    def __post_init__(self) -> None:
        if self.Type != MessageType.FetchAllBundlesResponse:
            raise InvalidMessageError(
                f"Message needs MessageType {MessageType.FetchAllBundlesResponse}, but has {self.Type}"
            )

    @override
    def dictify(self) -> dict:
        parent_dict = super().dictify()
        own_dict = {
            "Bundles": [bundle_content.dictify() for bundle_content in self.Bundles]
        }
        return parent_dict | own_dict

    @classmethod
    def from_dict(cls, data) -> FetchAllBundlesResponse:
        data["Bundles"] = [
            BundleContent.from_dict(bundle_content)
            for bundle_content in data["Bundles"]
        ]
        return cls(**data)


@dataclass(frozen=True)
class BundleContent:
    BundleID: str
    SourceID: EID
    DestinationID: EID
    Payload: bytes = b""

    def dictify(self) -> dict:
        data = {key: value for key, value in self.__dict__.items() if value}
        return data

    @classmethod
    def from_dict(cls, data: dict) -> BundleContent:
        data["SourceID"] = EID(data["SourceID"])
        data["DestinationID"] = EID(data["DestinationID"])

        return cls(**data)


def serialize(message: Message) -> bytes:
    """
    Serializes message for transmission

    Args:
        message: Message to be serialized

    Returns:
        Bytes of serialized message

    Raises:
        ormsgpack.MsgpackEncodeError: if message is not serializable
    """

    data = message.dictify()
    return packb(data)


MESSAGE_CONSTRUCTORS: dict[MessageType, Callable[[dict], Message]] = {
    MessageType.Response: Response.from_dict,
    MessageType.RegisterEID: RegisterUnregister.from_dict,
    MessageType.UnregisterEID: RegisterUnregister.from_dict,
    MessageType.BundleCreate: BundleCreate.from_dict,
    MessageType.BundleCreateResponse: BundleCreateResponse.from_dict,
    MessageType.ListBundles: ListBundles.from_dict,
    MessageType.ListResponse: ListResponse.from_dict,
    MessageType.FetchBundle: FetchBundle.from_dict,
    MessageType.FetchBundleResponse: FetchBundleResponse.from_dict,
    MessageType.FetchAllBundles: FetchAllBundles.from_dict,
    MessageType.FetchAllBundlesResponse: FetchAllBundlesResponse.from_dict,
}


def deserialize(serialized: bytes) -> Message:
    """
    Deserializes bytes into a message object

    Args:
        serialized: Message in serialized form

    Returns:
        Deserialized message - will be a subclass of Message

    Raises:
        ormsgpack.MsgpackDecodeError: if the object is of an invalid type or is not valid MessagePack
        InvalidMessageError: if deserialized message has no "Type" field
        InvalidMessageError: if deserialized message has the "Type" field, but the contained value is unknown/we don't know the corresponding message format
        InvalidMessageError: if sanity-checks for the deserialized message fail
    """

    data_dict: dict = unpackb(serialized)

    if "Type" not in data_dict:
        raise InvalidMessageError("Message missing 'Type' field")

    try:
        msg_type = MessageType(data_dict["Type"])
    except ValueError:
        raise InvalidMessageError(f"Unknown MessageType ID: {data_dict['Type']}")

    if msg_type not in MESSAGE_CONSTRUCTORS:
        raise InvalidMessageError(f"No constructor defined for {msg_type}")

    return MESSAGE_CONSTRUCTORS[msg_type](data_dict)
