from influxdb import DataFrameClient
from datetime import datetime, timedelta
from typing import List
import pandas as pd
import numpy as np
from math import sin, cos, sqrt, atan2, radians

from OverviewDatabase import OverviewDatabase
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

        # Drop NaN
        res_pd.dropna(axis=0, inplace=True)
        return res_pd
    latitude = query("gps_measure/latitude")
    longitude = query("gps_measure/longitude")
    altitude = query("gps_measure/altitude")
    speed = query("gps_measure/speed")


    # Clean the values to one specific DataFrame
    results = pd.DataFrame()
    results = latitude.copy()
    results.rename(columns={"index": "index", "mean": "latitude"}, inplace=True) # rename for latitude
    results["longitude"] = longitude["mean"]
    results["altitude"] = altitude["mean"]
    results["speed"] = speed["mean"]
    results["km"] = 0 # Fill the km of 0

    # Remove duplicates (if the vehicle hasn't moved)
    c_maxes = results.groupby(['latitude', 'longitude']).C.transform(max)
    results = results.loc[results.C == c_maxes]

    # Remove data when the vehicle hasn't moved based on its speed
    results.drop(results[results["speed"] < 0.1].index[1:], inplace=True) # Remove all but the first

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


legend_html = """
{{% macro html(this, kwargs) %}}
<!doctype html>
<html lang="fr">
<body>
<div id='maplegend' class='maplegend'
    style='position: fixed; z-index:9999; border:2px solid grey; background-color:rgba(255, 255, 255, 0.8);
    border-radius:6px; padding: 10px;
    bottom: 10px;
    left: 10px;
    width: 180px;
    height: 120px;
    z-index:9998;
    font-size:14px;
    background-color: #ffffff;
    opacity: 0.7;'>
    
<div class='legend-title'>Trip overview</div>
<div class='legend-scale'>
  <ul class='legend-labels'>
    <li>{travel_day} jours depuis le départ</li>
    <li>{km} km parcouru</li>
    <li>{country_crossed} pays visités</li>
    <li>mise à jour le {last_update}</li>
  </ul>
</div>
</div>

<div id='desc' class='maplegend'
    style='position: fixed; z-index:9999; border:2px solid grey; background-color:rgba(255, 255, 255, 0.8);
    border-radius:6px; padding: 10px;
    bottom: 10px;
    left: 200px;
    width: 500px;
    height: 80px;
    z-index:9998;
    font-size:14px;
    background-color: #ffffff;
    opacity: 0.7;'>
    
<div class='legend-title'>Description</div>
<div class='legend-scale'>
  <ul class='legend-labels'>
    <li>Voici une vue à jour du parcours de la capsule sur la carte du monde ! </li>
    <li>Voyageurs: Laurence et Emmanuel Rudloff</li>
  </ul>
</div>
</div>
</body>
</html>

<style type='text/css'>
  .maplegend .legend-title {{
    text-align: left;
    margin-bottom: 5px;
    font-weight: bold;
    font-size: 90%;
    }}
  .maplegend .legend-scale ul {{
    margin: 0;
    margin-bottom: 5px;
    padding: 0;
    float: left;
    list-style: none;
    }}
  .maplegend .legend-scale ul li {{
    font-size: 80%;
    list-style: none;
    margin-left: 0;
    line-height: 18px;
    margin-bottom: 2px;
    }}
  .maplegend ul.legend-labels li span {{
    display: block;
    float: left;
    height: 16px;
    width: 30px;
    margin-right: 5px;
    margin-left: 0;
    border: 1px solid #999;
    }}
  .maplegend .legend-source {{
    font-size: 80%;
    color: #777;
    clear: both;
    }}
  .maplegend a {{
    color: #777;
    }}
</style>
{{% endmacro %}}"""

def create_site(trip_data: OverviewDatabase, site_folder: str, date, url):
    gps_trace = trip_data.get_road_trip_gps_trace()
    center_of_map = gps_trace[["latitude", "longitude"]].iloc[-1].tolist() # Last updated GPS position
    whole_trip_trace = gps_trace[["latitude", "longitude"]]
    
    # Maps
    offline_map = [folium.Map(center_of_map, tiles=url, attr="Capsule map"), "offline"]
    online_map = [folium.Map(center_of_map, tiles="OpenStreetMap", attr="Capsule map"), "online"]

    for map_data in [offline_map, online_map]:
        map = map_data[0]

        # Markers group
        sleep_position_group = folium.FeatureGroup(name="Campements")
        kw = {"prefix": "fa", "color": "blue", "icon": "bed"}
        html = '<h1>{date}</h1><p>Etape {step}</p><p>Distance parcourue {km} km</p><p>Coordonnée GPS: {lat}, {lon}</p>'
        icon = folium.Icon(**kw)

        # TODO Handle case where the sub step trace length is not > 1
        for current_step_trace_idx in range(gps_trace.index.values[-1] + 1):
            current_step_trace = gps_trace.loc[current_step_trace_idx]
            if len(current_step_trace) > 1:
                distance_traveled_in_step = current_step_trace["km"].iloc[-1] - current_step_trace["km"].iloc[0]
                date = current_step_trace["date"].iloc[0].day
                """gif = "test.gif" # TODO
                tooltip_html = '<h1>{date}</h1><p>Etape {step}</p><p>Distance parcourue {distance} km</p><img src={gif}>'\
                    .format(date=distance_traveled_in_step,
                            step=current_step_trace_idx,
                            distance=distance_traveled_in_step,
                            gif=gif)"""
                folium.plugins.AntPath(
                    locations=current_step_trace[["latitude", "longitude"]],
                    dash_array=[10, 15],
                    delay=800,
                    weight=6,
                    color="#F6FFF3",
                    pulse_color="#000000",
                    paused=False,
                    reverse=False,
                    #tooltip=tooltip_html TODO
                ).add_to(map)
            current_sleep_location = current_step_trace[["latitude", "longitude"]].iloc[-1].values
            
            folium.Marker(list(current_sleep_location),
            icon=icon, tooltip=html.format(
                date=datetime.datetime.strftime(current_step_trace["date"].iloc[-1], "%d %B %Y"),
                step=current_step_trace_idx+1,
                km=round(current_step_trace["km"].iloc[-1], 1),
                lat=current_sleep_location[0], 
                lon=current_sleep_location[1])).add_to(sleep_position_group)

        # Add markers to map
        sleep_position_group.add_to(map)
        folium.LayerControl().add_to(map)
        folium.plugins.LocateControl().add_to(map)

        # Add fullscreen function
        folium.plugins.Fullscreen(
            title="Agrandir",
            title_cancel="Annuler",
            force_separate_button=True,
        ).add_to(map)

                
        legend = branca.element.MacroElement()
        legend._template = branca.element.Template(
            legend_html.format(
                travel_day= (gps_trace["date"].iloc[-1]-gps_trace["date"].iloc[0]).days, 
                km=round(gps_trace["km"].iloc[-1], 1), 
                country_crossed= len(gps_trace["current_country"].value_counts()), 
                last_update="10 jun"))
        map.get_root().add_child(legend)

        # Limit bounds
        map.fit_bounds(map.get_bounds())

        map.save(site_folder+"saves/"+map_data[1]+"_"+date+".html")
        print("Saved in ", site_folder+"saves/"+map_data[1]+"_"+date+".html")
        map.save(site_folder+map_data[1]+"_index.html")
        print("Saved in ", site_folder+map_data[1]+"_index.html")