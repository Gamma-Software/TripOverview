#!/usr/bin/python3
import argparse
import typing
import sys


def save_gps_position(gps_position):
    print("save_position")


def create_site():
    print("create site")


def manual():
    print("Create a map in html, save gps position")


def parse_args(cmd_args: typing.Sequence[str]):
    parser = argparse.ArgumentParser(prog='overview')
    parser.add_argument('--version', help='Prints Overview\'s version', action="store_true")
    subparsers = parser.add_subparsers(help='sub-command help')

    save_gps_position_parser = subparsers.add_parser('save_gps_position', help='Save GPS position')
    save_gps_position_parser.add_argument('gps_position', type=str, help='gps_position [latitude, longitudinal,'
                                                                         ' elevation]')
    save_gps_position_parser.set_defaults(func=save_gps_position)

    create_site_parser = subparsers.add_parser('create_site', help="Generate the web site to display the photos and"
                                                                   " current trip")
    create_site_parser.set_defaults(func=create_site)

    parser_man = subparsers.add_parser("man", help="Open overview manual")
    parser_man.set_defaults(func=manual)

    parser.set_defaults(func=lambda x: parser.print_help())
    return parser.parse_args(args=cmd_args)


def main_args(cmd_args: typing.Sequence[str]):
    args = parse_args(cmd_args)
    sys.exit(args.func(args))


def main():
    main_args(sys.argv[1:])
