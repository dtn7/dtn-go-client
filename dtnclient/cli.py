#! /usr/bin/env python3

import argparse
import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dtnclient.client import (
    DataError,
    DTNDError,
    create_bundle,
    fetch_all_bundles,
    fetch_bundle,
    list_bundles,
    register_unregister,
)
from dtnclient.eid import EID


@dataclass(frozen=True)
class MaxLevelFilter(logging.Filter):
    max_level: int

    def filter(self, record: logging.LogRecord):
        return record.levelno <= self.max_level


def _cli_no_command(_: argparse.Namespace) -> None:
    logging.error("Must choose a command")
    sys.exit(1)


def _cli_register(args: argparse.Namespace) -> None:
    try:
        register_unregister(
            socket_path=args.socket, eid=args.EndpointID, register=not args.unregister
        )
        logging.info("success")
    except FileNotFoundError:
        logging.error("Could not connect to agent socket")
        sys.exit(1)
    except DataError as err:
        logging.error(f"Error communicating with dtnd: {err}")
        sys.exit(1)
    except DTNDError as err:
        logging.error(f"dtnd responded with error: {err}")
        sys.exit(1)
    except Exception as err:
        logging.error(f"Generic error: {err}")
        sys.exit(1)


def _cli_create(args: argparse.Namespace) -> None:
    try:
        bundle_args: dict[str, Any] = {
            "source": args.source,
            "destination": args.destination,
            "lifetime": args.lifetime,
        }

        if args.report_to:
            bundle_args["report_to"] = args.report_to

        if args.timestamp == "now":
            bundle_args["creation_timestamp_now"] = True
        elif args.timestamp == "epoch":
            bundle_args["creation_timestamp_epoch"] = True
        else:
            bundle_args["creation_timestamp_time"] = args.timestamp

        payload: bytes = b""
        if args.payload == "stdin":
            payload = sys.stdin.read().encode("utf-8")
        else:
            with open(args.payload, "rb") as f:
                payload = f.read()
        bundle_args["payload_block"] = payload

        bundle_id = create_bundle(socket_path=args.socket, args=bundle_args)

        logging.info(bundle_id)
    except FileNotFoundError as err:
        logging.error(err)
        sys.exit(1)
    except DataError as err:
        logging.error(f"Error communicating with dtnd: {err}")
        sys.exit(1)
    except DTNDError as err:
        logging.error(f"dtnd responded with error: {err}")
        sys.exit(1)
    except Exception as err:
        logging.error(f"Generic error: {err}")
        sys.exit(1)


def _cli_list(args: argparse.Namespace) -> None:
    try:
        bundles = list_bundles(
            socket_path=args.socket, mailbox=args.mailbox, new_only=args.new
        )
        logging.info(bundles)
    except FileNotFoundError:
        logging.error("Could not connect to agent socket")
        sys.exit(1)
    except DataError as err:
        logging.error(f"Error communicating with dtnd: {err}")
        sys.exit(1)
    except DTNDError as err:
        logging.error(f"dtnd responded with error: {err}")
        sys.exit(1)
    except Exception as err:
        logging.error(f"Generic error: {err}")
        sys.exit(1)


def _cli_fetch_single(args: argparse.Namespace) -> None:
    try:
        bundle = fetch_bundle(
            socket_path=args.socket,
            mailbox=args.mailbox,
            bundle_id=args.bundle_id,
            delete=args.delete,
        )

        if hasattr(args, "filename") and args.filename:
            with open(args.filename, "wb") as f:
                f.write(bundle.Payload)
            logging.info("success")
        else:
            print(bundle.Payload)

    except FileNotFoundError as err:
        logging.error(err)
        sys.exit(1)
    except DataError as err:
        logging.error(f"Error communicating with dtnd: {err}")
        sys.exit(1)
    except DTNDError as err:
        logging.error(f"dtnd responded with error: {err}")
        sys.exit(1)
    except Exception as err:
        logging.error(f"Generic error: {err}")
        sys.exit(1)


def _cli_fetch_all(args: argparse.Namespace) -> None:
    try:
        bundles = fetch_all_bundles(
            socket_path=args.socket,
            mailbox=args.mailbox,
            new_only=args.new,
            delete=args.delete,
        )

        prefix: Path
        if hasattr(args, "directory") and args.directory:
            prefix = args.directory
            prefix.mkdir(parents=True, exist_ok=True)
        else:
            prefix = Path(".")

        for bundle in bundles:
            sanitized_name = bundle.BundleID.replace("/", "")
            with open(prefix / sanitized_name, "wb") as f:
                f.write(bundle.Payload)

    except FileNotFoundError as err:
        logging.error(err)
        sys.exit(1)
    except DataError as err:
        logging.error(f"Error communicating with dtnd: {err}")
        sys.exit(1)
    except DTNDError as err:
        logging.error(f"dtnd responded with error: {err}")
        sys.exit(1)
    except Exception as err:
        logging.error(f"Generic error: {err}")
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Interact with dtnd")

    parser.add_argument(
        "-s",
        "--socket",
        help="Path to the dtn application-agent's socket",
    )
    parser.add_argument("-v", action="store_true", help="verbose logging")
    parser.set_defaults(run=_cli_no_command)

    subparsers = parser.add_subparsers()

    register_parser = subparsers.add_parser(
        name="register", help="Perform (un)registrations of EndpointIDs"
    )
    register_parser.set_defaults(run=_cli_register)
    register_parser.add_argument(
        "EndpointID", help="EndpointID to (un)register", type=EID
    )
    register_parser.add_argument(
        "-u",
        "--unregister",
        action="store_true",
        help="Perform unregistration rather than registration",
    )

    create_parser = subparsers.add_parser(name="create", help="Create a new bundle")
    create_parser.set_defaults(run=_cli_create)
    create_parser.add_argument(
        "-s", "--source", required=True, type=EID, help="Bundle's source EID"
    )
    create_parser.add_argument(
        "-d", "--destination", required=True, type=EID, help="Bundle's destination EID"
    )
    create_parser.add_argument(
        "-r",
        "--report_to",
        required=False,
        type=EID,
        default=EID.none(),
        help="Send status reports to this EID (optional)",
    )
    create_parser.add_argument(
        "-t",
        "--timestamp",
        required=False,
        default="now",
        help="Override bundle's creation timestamp. Can be either 'now' (default), 'epoch' for 1.1.1970, or an arbitrary value",
    )
    create_parser.add_argument(
        "-l",
        "--lifetime",
        required=False,
        default="24h",
        help="Bundle's lifetime (optional)",
    )
    create_parser.add_argument(
        "-p",
        "--payload",
        required=False,
        default="stdin",
        help="Bundle's payload, either a filename to read or 'stdin'",
    )

    list_parser = subparsers.add_parser(
        name="list", help="List bundles stored in a mailbox"
    )
    list_parser.set_defaults(run=_cli_list)
    list_parser.add_argument(
        "mailbox", type=EID, help="EndpointID of the mailbox that we want to check"
    )
    list_parser.add_argument(
        "-n", "--new", action="store_true", help="Only list new bundles"
    )

    fetch_parser = subparsers.add_parser(name="fetch", help="Fetch bundles from store")
    fetch_parser.set_defaults(run=_cli_no_command)
    fetch_parser.add_argument("mailbox", type=EID, help="Fetch from this mailbox")
    fetch_parser.add_argument(
        "-d", "--delete", action="store_true", help="Delete bundle after fetching"
    )
    fetch_subparsers = fetch_parser.add_subparsers()

    fetch_single = fetch_subparsers.add_parser(
        name="single", help="Fetch single bundle by BundleID"
    )
    fetch_single.set_defaults(run=_cli_fetch_single)
    fetch_single.add_argument("bundle_id", help="BundleID to fetch")
    fetch_single.add_argument(
        "-f",
        "--filename",
        required=False,
        help="Filename to write bundle payload to. If unset, will print ot stdout",
    )

    fetch_all = fetch_subparsers.add_parser(name="all", help="Fetch all bundles")
    fetch_all.set_defaults(run=_cli_fetch_all)
    fetch_single.add_argument(
        "-d",
        "--directory",
        required=False,
        type=Path,
        help="Directory to write bundle payloads to. Will use BundleIDs as filenames. If unset, will use current directory.",
    )
    fetch_all.add_argument(
        "-n", "--new", action="store_true", help="Only fetch new bundles"
    )

    args = parser.parse_args()

    log_level = logging.DEBUG if args.v else logging.INFO

    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Handler for DEBUG, INFO, WARNING  -> stdout
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.DEBUG)
    stdout_handler.addFilter(MaxLevelFilter(logging.WARNING))

    # Handler for ERROR, CRITICAL       -> stderr
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(logging.ERROR)

    fmt = logging.Formatter("%(message)s")
    stdout_handler.setFormatter(fmt)
    stderr_handler.setFormatter(fmt)

    logger.addHandler(stdout_handler)
    logger.addHandler(stderr_handler)

    args.run(args)


if __name__ == "__main__":
    main()
