from influxdb import DataFrameClient
from datetime import datetime, timedelta
from typing import List
import pandas as pd


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
    #km = query("odometry/km")

    # Clean the values to one specific DataFrame
    results = pd.DataFrame()
    results = latitude.copy()
    results["longitude"] = longitude["mean"]
    results["altitude"] = altitude["mean"]
    results["speed"] = speed["mean"]
    results["km"] = speed["mean"] # TODO replace with km when ready
    results.columns = ["latitude", "longitude", "altitude", "speed", "km"]

    # Filter out only on timestamps
    mask = (results.index >= timestamps[0]) & (results.index <= timestamps[-1])

    results['current_step'] = [0]*len(results.index) # TODO for now the current step will always be 0
    results['timestamp'] = results.index # Reset index to get timestamp as a column
    results["timestamp"] = results["timestamp"].apply(lambda x: int(datetime.fromisoformat(str(x)).timestamp()))

    results.astype({"km": int}) # set km as int

    return results.loc[mask]


from OverviewDatabase import OverviewDatabase
import folium
import folium.plugins
import base64
import branca

def create_site(trip_data: OverviewDatabase, site_folder: str, date, url):
    gps_trace = trip_data.get_road_trip_gps_trace()
    center_of_map = tuple(gps_trace.tail(1)[["latitude", "longitude"]].iloc[0].values.tolist())
    whole_trip_trace = gps_trace[["latitude", "longitude"]]
    map_to_plot = folium.Map(center_of_map, zoom_start=10, tiles=url, attr="Capsule map")

    # TODO Handle case where the sub step trace length is not > 1
    for current_step_trace_idx in range(gps_trace.index.values[-1]):
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
               '<p>Coordonnée GPS: {lat}, {lon}</p>'.format(date=sleep_steps["date"].iloc[i].day,
                                                            step=sleep_steps["current_step"].iloc[i].value,
                                                            distance=sleep_steps["km"].iloc[i].value,
                                                            lat=sleep_steps["latitude"].iloc[i].value,
                                                            lon=sleep_steps["longitude"].iloc[i].value)
        icon = folium.Icon(**kw)
        folium.Marker(location=sleep_steps[["latitude", "longitude"]][i], icon=icon, tooltip=html).add_to(marker_cluster_steps)

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

    map_to_plot.save(site_folder+date+".html")