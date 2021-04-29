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
import branca

from src.overview.OverviewDatabase import OverviewDatabase

trip_data = OverviewDatabase()
path_to_conf = os.path.join(os.path.expanduser("~"), ".trip_overview/configuration.yaml") \
    if platform.system() == "Linux" else os.path.join(os.path.expanduser("~"), ".trip_overview\\configuration.yaml")


def save_gps_position(timestamp, lat, lon, elev, speed, km):
    trip_data.commit_position(timestamp, lat, lon, elev, speed, km)


def create_site():
    gps_trace = trip_data.get_road_trip_gps_trace()
    center_of_map = gps_trace[-1]
    whole_trip_trace = gps_trace[["lat", "lon"]]
    map_to_plot = folium.Map(center_of_map, zoom_start=10)

    # TODO Handle case where the sub step trace length is not > 1
    for current_step_trace_idx in range(gps_trace.current_step.iloc[-1].value):
        current_step_trace = gps_trace.loc[current_step_trace_idx]
        if len(current_step_trace) > 1:
            distance_traveled_in_step = 0
            for km_idx in range(1, len(current_step_trace["km"])):
                distance_traveled_in_step += current_step_trace["km"][km_idx] - current_step_trace["km"][km_idx - 1]
            date = current_step_trace["date"][0].day
            gif = "test.gif" # TODO
            tooltip_html = '<h1>{date}</h1><p>Etape {step}</p><p>Distance parcourue {distance} km</p><img src={gif}>'\
                .format(date=distance_traveled_in_step,
                        step=current_step_trace_idx,
                        distance=distance_traveled_in_step,
                        gif=gif)
            folium.plugins.AntPath(
                locations=current_step_trace,
                dash_array=[10, 15],
                delay=800,
                weight=6,
                color="#F6FFF3",
                pulse_color="#000000",
                paused=False,
                reverse=False,
                tooltip=tooltip_html
            ).add_to(map_to_plot)

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
    # TODO get from instagram
    for i in range(0, len(whole_trip_trace), 200):
        html = '<h1>{date}</h1><p>Etape {step}</p><p>Distance parcourue {distance} km</p>' \
               '<p>Coordonnée GPS: {lat}, {lon}</p><p><img src="data:image/jpeg;base64,{image}"></p>'.format(
            date="10 dec",
            step=10,
            distance=10,
            lat=10,
            lon=10,
            image=base64.b64encode(open("moon.jpg", 'rb').read()).decode('UTF-8')
        )
        icon = folium.Icon(**kw)
        folium.Marker(location=whole_trip_trace[i], icon=icon, tooltip=html).add_to(marker_cluster)

    kw = {"prefix": "fa", "color": "blue", "icon": "bed"}
    # Create sleep steps
    sleep_steps = trip_data.get_sleeping_locations()
    for i in range(len(sleep_steps)):
        html = '<h1>{date}</h1><p>Etape {step}</p><p>Distance parcourue {distance} km</p>' \
               '<p>Coordonnée GPS: {lat}, {lon}</p>'.format(date=sleep_steps.date.iloc[i].day,
                                                            step=sleep_steps.current_step.iloc[i].value,
                                                            distance=sleep_steps.km.iloc[i].value,
                                                            lat=sleep_steps.lat.iloc[i].value,
                                                            lon=sleep_steps.lon.iloc[i].value)
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
        <p>Temps de voyage: {number_day} jours</p>
        <p>Kilomètre parcourue: {distance} km</p>
        <p>Pays traversés: {country_passed}</p>
        <p>Date de mise à jour: {date_site_update}</p>
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
    """.format(number_day=10, distance=10, country_passed=10, date_site_update="10")

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

    # Limit bounds
    map_to_plot.fit_bounds(map_to_plot.get_bounds())

    map_to_plot.save(configuration["database_filepath"] + configuration["folium_site_output_filename"] + ".html")


def manual():
    print("Create a map in html, save gps position")


def configure():
    conf = load_config()[1]
    print("Write nothing and press ENTER to keep current configuration")
    print("configure kilometer_source:")
    choice = input("available configuration [\"GPS\" or \"ODO\"]:")
    conf["kilometer_source"] = choice if not "" else conf["kilometer_source"]
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
    with open(path_to_conf_win if platform.system() == "Windows" else path_to_conf_linux) as file:
        configuration = yaml.load(file, Loader=yaml.FullLoader)
    trip_data.connect_to_database(configuration["database_filepath"])

    args = parse_args(cmd_args)
    sys.exit(args.func(args))


def main():
    main_args(sys.argv[1:])
