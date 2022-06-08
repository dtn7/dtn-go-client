#! /usr/bin/env python3

import argparse
import sys
import base64
from dataclasses import dataclass
from typing import Any

import requests
import rapidjson as json

REQUEST_TIMEOUT = 60


@dataclass()
class RESTError(Exception):
    status_code: int
    error: str

    def __str__(self) -> str:
        return f"RESTError happened: {self.status_code} - {self.error}"


def load_payload(path: str) -> str:
    """Loads payload from specified file

    Args:
        path (str): Path to the file containing payload

    Returns:
        str: Content of payload file (encoded as base64 ist content was binary)
    """
    with open(path, "rb") as f:
        contents: bytes = f.read()
        return str(base64.b64encode(contents), encoding="utf-8")


def dump_payload(path: str, payload: str) -> None:
    with open(path, "wb") as f:
        f.write(base64.b64decode(bytes(payload, encoding="utf-8")))


def build_url(address: str, port: int) -> str:
    return f"http://{address}:{port}/rest"


def load_registration_data(path: str) -> dict[str, str]:
    with open(path, "r") as f:
        ids: dict[str, str] = json.load(f)
        return ids


def register(
    rest_url: str, endpoint_id: str, registration_data_file: str = ""
) -> dict[str, str]:
    """Registers the client with the REST Application Agent

    Args:
        rest_url: Address + Port+ Prefix for REST actions
        endpoint_id: BPv7 endpoint ID used for registration
        registration_data_file: If set, registration data will be written to a file

    Returns:
        Dictionary with two fields:
            "endpoint_id" contains the same value as was provided
            "uuid": token received from the server which is necessary for future actions

    Raises:
        RESTError if anything goes wrong
    """
    id_json = json.dumps({"endpoint_id": endpoint_id})
    response: requests.Response = requests.post(
        f"{rest_url}/register", data=id_json, timeout=REQUEST_TIMEOUT
    )
    if response.status_code != 200:
        raise RESTError(status_code=response.status_code, error=response.text)

    parsed_response = response.json()
    if parsed_response["error"]:
        raise RESTError(
            status_code=response.status_code, error=parsed_response["error"]
        )

    data = {"endpoint_id": endpoint_id, "uuid": parsed_response["uuid"]}
    marshaled = json.dumps(data)
    if registration_data_file:
        with open(registration_data_file, "w") as f:
            f.write(marshaled)
    return data


def _cli_register(rest_url: str, args: argparse.Namespace) -> None:
    """Perform registration with CLI-arguments

    Args:
        rest_url: Address + Port+ Prefix for REST actions
        args: Arguments provided by user

    Raises:
        RESTError if anything goes wrong

    """
    if not args.eid:
        print(
            "Must provide Endpoint ID",
            file=sys.stderr,
            flush=True,
        )
        sys.exit(1)

    registration_data = register(
        rest_url=rest_url,
        endpoint_id=args.eid,
        registration_data_file=args.registration_file,
    )
    if not args.registration_file:
        print(f"Registration data: {registration_data}")
    else:
        print(f"Registration data saved to: {args.registration_file}")


def fetch_pending(rest_url: str, uuid: str) -> list[dict[str, Any]]:
    """Fetch bundles addressed to this node

    Args:
        rest_url: Address + Port+ Prefix for REST actions
        uuid: Authentication token received via the register-method.

    Returns:
        List of all pending bundle's addressed to this node as a unmarshaled JSON object

    Raises:
        RESTError if anything goes wrong
    """
    response: requests.Response = requests.post(
        f"{rest_url}/fetch", data=json.dumps({"uuid": uuid}), timeout=REQUEST_TIMEOUT
    )
    if response.status_code != 200:
        raise RESTError(status_code=response.status_code, error=response.text)

    parsed_response = response.json()
    if parsed_response["error"]:
        raise RESTError(
            status_code=response.status_code, error=parsed_response["error"]
        )

    return parsed_response["bundles"]


def _cli_fetch_pending(rest_url: str, args: argparse.Namespace) -> None:
    if not args.registration_file and not args.uuid:
        print(
            "Must provide either registration file or uuid",
            file=sys.stderr,
            flush=True,
        )
        sys.exit(1)

    if args.registration_file:
        uuid = load_registration_data(args.registration_file)["uuid"]
    else:
        uuid = args.uuid

    pending = fetch_pending(rest_url=rest_url, uuid=uuid)

    for bundle in pending:
        filename = f"{bundle['primaryBlock']['destination']}-{bundle['primaryBlock']['creationTimestamp']['date']}"
        filename = filename.replace("/", "")
        for block in bundle["canonicalBlocks"]:
            if block["blockTypeCode"] == 1:
                dump_payload(path=filename, payload=block["data"])


def _submit_bundle(rest_url: str, data: dict[str, Any]) -> None:
    response: requests.Response = requests.post(
        f"{rest_url}/build", data=json.dumps(data), timeout=REQUEST_TIMEOUT
    )
    if response.status_code != 200:
        raise RESTError(status_code=response.status_code, error=response.text)

    parsed_response = response.json()
    if parsed_response["error"]:
        raise RESTError(
            status_code=response.status_code, error=parsed_response["error"]
        )


def send_bundle(
    rest_url: str,
    uuid: str,
    source: str,
    destination: str,
    payload: str,
    lifetime: str = "24h",
) -> None:
    """Sends a bundle via the REST application agent

    Args:
        rest_url: http:// + Address + Port+ Prefix for REST actions
        uuid: Authentication token received via the register-method.
        source: BPv7 endpoint ID which will be set as the bundle's source.
                Needs to be one of the IDs of the agent's node
        destination: BPv7 endpoint ID which will be set as the bundle's destination
        payload: Bundle payload, should be a plaintext string or base64 encoded binary data
        lifetime: Time until the bundle expires and is deleted from node stores

    Raises:
        RESTError if anything goes wrong
    """
    data = {
        "uuid": uuid,
        "arguments": {
            "destination": destination,
            "source": source,
            "creation_timestamp_now": 1,
            "lifetime": lifetime,
            "payload_block": payload,
        },
    }
    _submit_bundle(rest_url=rest_url, data=data)


def _cli_send_bundle(rest_url: str, args: argparse.Namespace) -> None:
    if not args.registration_file and not (args.endpoint_id and args.uuid):
        print(
            "Must provide either registration file OR (EndpointID AND uuid)",
            file=sys.stderr,
            flush=True,
        )
        sys.exit(1)

    if not args.destination:
        print(
            "Must provide bundle destination",
            file=sys.stderr,
            flush=True,
        )
        sys.exit(1)

    if args.registration_file:
        reg_data = load_registration_data(args.registration_file)
        source = reg_data["endpoint_id"]
        uuid = reg_data["uuid"]
    else:
        source = args.endpoint_id
        uuid = args.uuid

    if args.payload:
        payload = load_payload(args.payload)
    else:
        payload = sys.stdin.read()

    send_bundle(
        rest_url=rest_url,
        uuid=uuid,
        source=source,
        destination=args.destination,
        payload=payload,
        lifetime=args.lifetime,
    )


def _cli_no_command(rest_url: str, args: argparse.Namespace) -> None:
    print(
        "Must choose a command",
        file=sys.stderr,
        flush=True,
    )
    sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Interact with dtnd")
    parser.add_argument(
        "-a", "--address", default="localhost", help="Address of the REST-Agent"
    )
    parser.add_argument(
        "-p", "--port", type=int, default=8080, help="Port of the REST-Agent"
    )
    parser.set_defaults(func=_cli_no_command)

    subparsers = parser.add_subparsers(help="Commands")

    register_parser = subparsers.add_parser("register", help="Register with dtnd")
    register_parser.set_defaults(func=_cli_register)
    register_parser.add_argument("eid", help="Endpoint ID for registration")
    register_parser.add_argument(
        "-r",
        "--registration_file",
        default="",
        help="Write registration data to a file",
    )

    fetch_parser = subparsers.add_parser(
        "fetch", help="Fetch bundles for our Endpoint-ID"
    )
    fetch_parser.add_argument(
        "-r", "--registration_file", default="", help="Load registration data from file"
    )
    fetch_parser.add_argument(
        "-u", "--uuid", default="", help="Manually provide registration UUID"
    )
    fetch_parser.set_defaults(func=_cli_fetch_pending)

    send_parser = subparsers.add_parser("send", help="Send bundle")
    send_parser.add_argument(
        "-r", "--registration_file", default="", help="Load registration data from file"
    )
    send_parser.add_argument(
        "-e", "--endpoint_id", default="", help="Manually set Endpoint ID"
    )
    send_parser.add_argument(
        "-u", "--uuid", default="", help="Manually provide registration UUID"
    )
    send_parser.add_argument("-p", "--payload", default="", help="Payload file")
    send_parser.add_argument(
        "-l", "--lifetime", default="24h", help="Lifetime of bundle"
    )
    send_parser.add_argument("destination", help="Endpoint ID of recipient")
    send_parser.set_defaults(func=_cli_send_bundle)

    args = parser.parse_args()

    rest_url = build_url(address=args.address, port=args.port)

    args.func(rest_url=rest_url, args=args)
