from typing_extensions import runtime
from influxdb import DataFrameClient
from datetime import datetime, timedelta
from typing import List
import pandas as pd
import numpy as np
from math import sin, cos, sqrt, atan2, radians

from src.overview.OverviewDatabase import OverviewDatabase
import folium
import folium.plugins
import base64
import branca

def dist_from_gps(coord_a, coord_b):
    """
    Haversine’s algorithm
    param: decimal gps coord_a [lat, lon]
    param: decimal gps coord_b [lat, lon]
    result: distance between two gps coords
    """
    R = 6373.0 # approximate radius of earth in km

    lat1 = radians(coord_a[0])
    lon1 = radians(coord_a[1])
    lat2 = radians(coord_b[0])
    lon2 = radians(coord_b[1])

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return R * c

def retrieve_influxdb_data(timestamps,  influxdb_client: DataFrameClient, resampling_time: str) -> pd.DataFrame():
    start = (datetime.fromisoformat(timestamps[0]) + timedelta(seconds=-5)).isoformat()
    end = (datetime.fromisoformat(timestamps[-1]) + timedelta(seconds=5)).isoformat()
    # Query the lat and lon values inside of the first and last + margin timestamps
    def query(topic: str):    
        result = influxdb_client.query("SELECT MEAN(\"value\") FROM \"autogen\".\"mqtt_consumer\" WHERE (\"topic\"\
            = '"+topic+"') AND time >= '"+start+"Z' AND time <= '"+end+"Z' GROUP BY time("+resampling_time+") fill(previous)")
        res_pd = pd.DataFrame()
        if result:
            res_pd = result["mqtt_consumer"]
        return res_pd
    latitude = query("gps_measure/latitude")
    longitude = query("gps_measure/longitude")
    altitude = query("gps_measure/altitude")
    speed = query("gps_measure/speed")

    # Clean the values to one specific DataFrame
    results = pd.DataFrame()
    results = latitude.copy()
    results["longitude"] = longitude["mean"]
    results["altitude"] = altitude["mean"]
    results["speed"] = speed["mean"]
    results["km"] = 0 # Fill the km of 0
    # This is computed from the last and current gps position
    for i in range(1, len(results["longitude"])):
        results["km"].iloc[i] = results["km"].iloc[i-1] + dist_from_gps(
            [results["latitude"].iloc[i-1], results["longitude"].iloc[i-1]],
            [results["latitude"].iloc[i], results["longitude"].iloc[i]]) # TODO Call from df can be optimized
    results.columns = ["latitude", "longitude", "altitude", "speed", "km"] # Sort correctly the columns

    # Filter out only on timestamps
    mask = (results.index >= timestamps[0]) & (results.index <= timestamps[-1])

    results['current_step'] = [0]*len(results.index) # TODO for now the current step will always be 0
    results['timestamp'] = results.index # Reset index to get timestamp as a column
    results["timestamp"] = results["timestamp"].apply(lambda x: int(datetime.fromisoformat(str(x)).timestamp()))

    results.astype({"km": int}) # set km as int

    return results.loc[mask]


def create_site(trip_data: OverviewDatabase, site_folder: str, date, url):
    gps_trace = trip_data.get_road_trip_gps_trace()
    center_of_map = gps_trace[["latitude", "longitude"]].iloc[-1].tolist() # Last updated GPS position
    whole_trip_trace = gps_trace[["latitude", "longitude"]]
    offline_map = [folium.Map(center_of_map, tiles=url, attr="Capsule map"), "offline"]
    online_map = [folium.Map(center_of_map, tiles="OpenStreetMap", attr="Capsule map"), "online"]

    for map_data in [offline_map, online_map]:
        map = map_data[0]
        # TODO Handle case where the sub step trace length is not > 1
        for current_step_trace_idx in range(gps_trace.index.values[-1]):
            current_step_trace = gps_trace.loc[current_step_trace_idx]
            if len(current_step_trace) > 1:
                distance_traveled_in_step = 0
                for km_idx in range(1, len(current_step_trace["km"])):
                    distance_traveled_in_step += current_step_trace["km"][km_idx] - current_step_trace["km"][km_idx - 1]
                date = current_step_trace["date"][0].day
                """gif = "test.gif" # TODO
                tooltip_html = '<h1>{date}</h1><p>Etape {step}</p><p>Distance parcourue {distance} km</p><img src={gif}>'\
                    .format(date=distance_traveled_in_step,
                            step=current_step_trace_idx,
                            distance=distance_traveled_in_step,
                            gif=gif)"""
                folium.plugins.AntPath(
                    locations=current_step_trace,
                    dash_array=[10, 15],
                    delay=800,
                    weight=6,
                    color="#F6FFF3",
                    pulse_color="#000000",
                    paused=False,
                    reverse=False,
                    #tooltip=tooltip_html TODO
                ).add_to(map)

        folium.LayerControl(collapsed=False).add_to(map)

        folium.plugins.LocateControl().add_to(map)

        folium.plugins.Fullscreen(
            title="Agrandir",
            title_cancel="Annuler",
            force_separate_button=True,
        ).add_to(map)

        # Limit bounds
        map.fit_bounds(map.get_bounds())

        map.save(site_folder+"saves/"+map_data[1]+"_"+date+".html")
        print("Saved in ", site_folder+"saves/"+map_data[1]+"_"+date+".html")
        map.save(site_folder+map_data[1]+"_index.html")
        print("Saved in ", site_folder+map_data[1]+"_index.html")