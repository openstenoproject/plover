import argparse
import sys

from plover import log
from plover.oslayer.controller import Controller


def main():
    description = 'Send a command to a running Plover instance.'
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-l', '--log-level', choices=['debug', 'info', 'warning', 'error'],
                        default=None, help='set log level')
    parser.add_argument('command', metavar='COMMAND{:ARGS}',
                        type=str, help='the command to send')
    args = parser.parse_args(args=sys.argv[1:])
    if args.log_level is not None:
        log.set_level(args.log_level.upper())
    log.setup_platform_handler()
    with Controller() as controller:
        if controller.is_owner:
            log.error('sending command failed: no running instance found')
            sys.exit(1)
        controller.send_command(args.command)


if __name__ == '__main__':
    main()
