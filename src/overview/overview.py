#!/usr/bin/python3
import yaml
import argparse
import typing
import sys
import os
import platform
from shutil import copyfile
from src.overview.OverviewDatabase import OverviewDatabase

trip_data = OverviewDatabase()
path_to_conf_linux = os.path.join(os.path.expanduser("~"), "/.trip_overview/configuration.yaml")
path_to_conf_win = os.path.join(os.path.expanduser("~"), r"\.trip_overview\configuration.yaml")
configuration = dict()


def save_gps_position(timestamp, lat, lon, elev, speed, km):
    timestamp_geo_json.commit_position(timestamp, lat, lon, elev, speed, km)


def create_site():
    print("create site")


def manual():
    print("Create a map in html, save gps position")


def configure():
    # If the default configuration is not install, then configure w/ the default one
    if platform.system() == "Windows":
        src = os.path.join(os.getcwd(), "/data/default_configuration.yaml")
        path_to_conf = path_to_conf_linux
    else:
        src = os.path.join(os.getcwd(), r"\data\default_configuration.yaml")
        path_to_conf = path_to_conf_win
    if not os.path.exists(path_to_conf):
        print("The default configuration file is not installed")
        print("Add TripOverview default, ", src, " configuration to ", path_to_conf)
        copyfile(src, path_to_conf)

    # First print current configuration
    with open(path_to_conf) as file:
        conf = yaml.load(file, Loader=yaml.FullLoader)
        print("Current configuration:", conf)

    print("Write nothing and press enter to keep current configuration")
    print("configure kilometer_source:")
    choice = input("available configuration [\"GPS\" or \"ODO\"]:")
    conf["kilometer_source"] = choice if not "" else conf["kilometer_source"]
    print("configure database_filepath:")
    choice = input("")
    conf["database_filepath"] = choice if not "" else conf["database_filepath"]
    print("configure folium_site_output_path:")
    choice = input("")
    conf["folium_site_output_path"] = choice if not "" else conf["folium_site_output_path"]
    print("configure folium_site_output_filename (without html extension):")
    choice = input("")
    conf["folium_site_output_filename"] = choice if not "" else conf["folium_site_output_filename"]

    with open(path_to_conf, 'w') as file:
        documents = yaml.dump(conf, file)
        print("Write ", conf, " in ", path_to_conf)


def parse_args(cmd_args: typing.Sequence[str]):
    parser = argparse.ArgumentParser(prog='overview')
    parser.add_argument('--version', help='Prints Overview\'s version', action="store_true")
    subparsers = parser.add_subparsers(help='sub-command help')

    save_gps_position_parser = subparsers.add_parser('save_gps_position', help='Save GPS position')
    save_gps_position_parser.add_argument('timestamp', type=str)
    save_gps_position_parser.add_argument('latitude', type=float)
    save_gps_position_parser.add_argument('longitude', type=float)
    save_gps_position_parser.add_argument('speed', type=float, help="Speed of the vehicle in km/h")
    save_gps_position_parser.add_argument('km', type=int, help="Kilometer traveled")
    save_gps_position_parser.set_defaults(func=save_gps_position)

    create_site_parser = subparsers.add_parser('create_site', help="Generate the web site to display the photos and"
                                                                   " current trip")
    create_site_parser.set_defaults(func=create_site)

    parser_man = subparsers.add_parser("man", help="Open overview manual")
    parser_man.set_defaults(func=manual)

    parser.set_defaults(func=lambda x: parser.print_help())
    return parser.parse_args(args=cmd_args)


def main_args(cmd_args: typing.Sequence[str]):
    # load configuration
    with open(path_to_conf_linux if platform.system() == "Windows" else path_to_conf_win) as file:
        configuration = yaml.load(file, Loader=yaml.FullLoader)
    trip_data.connect_to_database(configuration["database_filepath"])

    args = parse_args(cmd_args)
    sys.exit(args.func(args))


def main():
    main_args(sys.argv[1:])
