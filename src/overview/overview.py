#!/usr/bin/python3
import yaml
import argparse
import typing
import sys
import os
import platform
from shutil import copyfile
import base64
import folium
import folium.plugins
import random
import branca

from src.overview.OverviewDatabase import OverviewDatabase

trip_data = OverviewDatabase()
path_to_conf_linux = os.path.join(os.path.expanduser("~"), "/.trip_overview/configuration.yaml")
path_to_conf_win = os.path.join(os.path.expanduser("~"), r"\.trip_overview\configuration.yaml")
configuration = dict()


def save_gps_position(timestamp, lat, lon, elev, speed, km):
    trip_data.commit_position(timestamp, lat, lon, elev, speed, km)


def create_site():
    center = (45.0, 2.0)
    gps_trace = trip_data.get_road_trip_gps_trace()
    whole_trip_trace = gps_trace[["lat", "lon"]]
    map_to_plot = folium.Map(gps_trace[-1], zoom_start=10)

    folium.plugins.AntPath(
        locations=whole_trip_trace,
        dash_array=[10, 15],
        delay=800,
        weight=6,
        color="#F6FFF3",
        pulse_color="#000000",
        paused=False,
        reverse=False,
        tooltip='<h1>10 Décembre 2021</h1><p>Etape X</p><p>Distance parcourue X km</p><img src="road.gif">'
    ).add_to(map_to_plot)
    map_to_plot.fit_bounds(map_to_plot.get_bounds())

    marker_cluster = folium.plugins.MarkerCluster(name='Photos during the trip').add_to(map_to_plot)
    marker_cluster_steps = folium.FeatureGroup(name="Etapes du voyage").add_to(map_to_plot)

    encoded = base64.b64encode(open("moon.jpg", 'rb').read())
    html = '<img src="data:image/jpeg;base64,{}">'.format
    resolution, width, height = 15, 50, 25
    iframe = folium.IFrame(html(encoded.decode('UTF-8')),
                           width=(width * resolution) + 20,
                           height=(height * resolution) + 20)
    popup = folium.Popup(iframe, max_height=1000)

    kw = {"prefix": "fa", "color": "green", "icon": "camera"}
    # Create photos marker
    for i in range(0, len(whole_trip_trace), 200):
        encoded = base64.b64encode(open("moon.jpg", 'rb').read())
        html = '<h1>10 Décembre 2021</h1><p>Etape X</p><p>Distance parcourue X km</p><p>Coordonnée GPS: {}, {}</p><p><img src="data:image/jpeg;base64,{}"></p>'.format
        icon = folium.Icon(**kw)
        folium.Marker(location=whole_trip_trace[i], icon=icon, tooltip=html(whole_trip_trace[i],
                                                            encoded.decode('UTF-8'))).add_to(marker_cluster)

    kw = {"prefix": "fa", "color": "blue", "icon": "bed"}
    # Create sleep steps
    sleep_steps = trip_data.get_sleeping_locations()
    for i in range(0, len(whole_trip_trace), 2000):
        html = '<h1>10 Décembre 2021</h1><p>Etape X</p><p>Distance parcourue X km</p><p>Coordonnée GPS: {}, {}</p>'.format(
            sleep_steps.lat.iloc[i].value, sleep_steps.lon.iloc[i].value)
        icon = folium.Icon(**kw)
        folium.Marker(location=sleep_steps[["lat", "lon"]][i], icon=icon, tooltip=html).add_to(marker_cluster_steps)

    legend_html = """
    {% macro html(this, kwargs) %}
    <div style="
        position: fixed;
        bottom: 10px;
        left: 10px;
        width: 250px;
        height: 100px;
        z-index:9999;
        font-size:14px;
        ">
        <p>Temps de voyage: 54 jours</p>
        <p>Kilomètre parcourue: 13141 km</p>
        <p>Pays traversés: 5</p>
        <p>Date de mise à jour: 10 mars 2021</p>
    </div>
    <div style="
        position: fixed;
        bottom: 0px;
        left: 0px;
        width: 250px;
        height: 120px;
        z-index:9998;
        font-size:14px;
        background-color: #ffffff;
        opacity: 0.7;
        ">
    </div>
    {% endmacro %}
    """

    legend = branca.element.MacroElement()
    legend._template = branca.element.Template(legend_html)
    map_to_plot.get_root().add_child(legend)

    folium.LayerControl(collapsed=False).add_to(map_to_plot)

    folium.plugins.LocateControl().add_to(map_to_plot)

    folium.plugins.Fullscreen(
        title="Agrandir",
        title_cancel="Annuler",
        force_separate_button=True,
    ).add_to(map_to_plot)
    map_to_plot.save(configuration["database_filepath"] + configuration["folium_site_output_filename"] + ".html")


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
