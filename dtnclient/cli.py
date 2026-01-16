#! /usr/bin/env python3

import argparse
import logging
import sys
from dataclasses import dataclass

from dtnclient.client import DataError, DTNDError, register_unregister
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
