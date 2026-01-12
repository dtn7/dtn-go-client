from __future__ import annotations

import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from enum import IntEnum
from typing import Any, override

from ormsgpack import packb, unpackb

from dtnclient.eid import EID

# (2^64)-1
MSGPACK_MAXINT = 18446744073709551615


class InvalidMessageError(ValueError):
    """Raised when a message is malformed"""


class InvalidBundleError(ValueError):
    """Raised when a bundle is malformed"""


class MessageType(IntEnum):
    GeneralResponse = 1
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
    type: MessageType

    def dictify(self) -> dict:
        return self.__dict__

    @classmethod
    def from_dict(cls, data) -> Message:
        return cls(**data)


@dataclass(frozen=True)
class GeneralResponse(Message):
    Error: str

    def __post_init__(self) -> None:
        if self.type != MessageType.GeneralResponse:
            raise InvalidMessageError(
                f"Message needs MessageType {MessageType.GeneralResponse}, but has {self.type}"
            )

    @override
    def dictify(self) -> dict:
        parent_dict = super().dictify()
        own_dict = self.__dict__
        return parent_dict | own_dict

    @classmethod
    def from_dict(cls, data) -> GeneralResponse:
        return cls(**data)


@dataclass(frozen=True)
class RegisterUnregister(Message):
    EndpointID: EID

    def __post_init__(self) -> None:
        if (
            self.type != MessageType.RegisterEID
            and self.type != MessageType.UnregisterEID
        ):
            raise InvalidMessageError(
                f"Message needs MessageType {MessageType.RegisterEID} or {MessageType.UnregisterEID}, but has {self.type}"
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
        if self.type != MessageType.BundleCreate:
            raise InvalidMessageError(
                f"Message needs MessageType {MessageType.BundleCreate}, but has {self.type}"
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
class BundleCreateResponse(GeneralResponse):
    BundleID: str

    def __post_init__(self) -> None:
        if self.type != MessageType.BundleCreateResponse:
            raise InvalidMessageError(
                f"Message needs MessageType {MessageType.BundleCreateResponse}, but has {self.type}"
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
        if self.type != MessageType.ListBundles:
            raise InvalidMessageError(
                f"Message needs MessageType {MessageType.ListBundles}, but has {self.type}"
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
class ListResponse(GeneralResponse):
    Bundles: list[str]

    def __post_init__(self) -> None:
        if self.type != MessageType.ListResponse:
            raise InvalidMessageError(
                f"Message needs MessageType {MessageType.ListResponse}, but has {self.type}"
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
        if self.type != MessageType.FetchBundle:
            raise InvalidMessageError(
                f"Message needs MessageType {MessageType.FetchBundle}, but has {self.type}"
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
class FetchBundleResponse(GeneralResponse):
    BundleContent: BundleContent

    def __post_init__(self) -> None:
        if self.type != MessageType.FetchBundleResponse:
            raise InvalidMessageError(
                f"Message needs MessageType {MessageType.FetchBundleResponse}, but has {self.type}"
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
        if self.type != MessageType.FetchAllBundles:
            raise InvalidMessageError(
                f"Message needs MessageType {MessageType.FetchAllBundles}, but has {self.type}"
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
class FetchAllBundlesResponse(GeneralResponse):
    Bundles: list[BundleContent]

    def __post_init__(self) -> None:
        if self.type != MessageType.FetchAllBundlesResponse:
            raise InvalidMessageError(
                f"Message needs MessageType {MessageType.FetchAllBundlesResponse}, but has {self.type}"
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
    Source: EID
    Destination: EID
    Payload: bytes = b""

    def dictify(self) -> dict:
        data = {key: value for key, value in self.__dict__.items() if value}
        return data

    @classmethod
    def from_dict(cls, data: dict) -> BundleContent:
        data["source"] = EID(data["source"])
        data["destination"] = EID(data["destination"])

        return cls(**data)


def serialize(message: Message) -> bytes:
    data = message.dictify()
    return packb(data)


MESSAGE_CONSTRUCTORS: dict[MessageType, Callable[[dict], Message]] = {
    MessageType.GeneralResponse: GeneralResponse.from_dict,
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
    try:
        data_dict: dict = unpackb(serialized)

        if "type" not in data_dict:
            raise InvalidMessageError("Message missing 'type' field")

        try:
            msg_type = MessageType(data_dict["type"])
        except ValueError:
            raise InvalidMessageError(f"Unknown MessageType ID: {data_dict['type']}")

        if msg_type not in MESSAGE_CONSTRUCTORS:
            raise InvalidMessageError(f"No constructor defined for {msg_type}")

        return MESSAGE_CONSTRUCTORS[msg_type](data_dict)

    except Exception as err:
        # Write the serialized data to a temp file for debugging
        prefix = "dtnclient_msg_dump_"

        with tempfile.NamedTemporaryFile(
            delete=False, prefix=prefix, suffix=".bin"
        ) as tmp_file:
            tmp_file.write(serialized)
            tmp_filename = tmp_file.name

        raise InvalidMessageError(
            f"Deserialization failed: {err}. Raw data dumped to {tmp_filename}"
        ) from err
