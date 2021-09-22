import sqlite3
from sqlite3 import Error
from sqlalchemy import create_engine
import pandas as pd
import geojson
import os
import io
import math
import reverse_geocoder


def distance(origin, destination):
    """
    Haversine formula example in Python
    Author: Wayne Dyck
    https://gist.github.com/rochacbruno/2883505
    """
    latitude1, longitude1 = origin
    latitude2, longitude2 = destination
    radius = 6371  # earth radius in km

    diff_latitude = math.radians(latitude2-latitude1)
    diff_longitude = math.radians(longitude2-longitude1)
    a = math.sin(diff_latitude/2) * math.sin(diff_latitude/2) + math.cos(math.radians(latitude1)) \
        * math.cos(math.radians(latitude2)) * math.sin(diff_longitude/2) * math.sin(diff_longitude/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    d = radius * c
    return d


class OverviewDatabase:
    """This class wraps the Folium TimestampGeoJson class to add functions like
    connecting to a database with simple custom geographic position.
    Usage:
     timestamp_geo_json = TimestampGeoJsonWrapper("file")
     timestamp_geo_json.query_positions()
     timestamp_geo_json.commit_position(...)
     timestamp_geo_json.close_database() (or called at destruction)"""

    # Database instance
    database = None
    raw_data = None
    kilometer_source = "GPS"  # Could be GPS (default) or ODO

    def __init__(self, kilometer_source="GPS"):
        """ Initiation """
        self.raw_data = None
        self.kilometer_source = kilometer_source

    def __del__(self):
        # Close the database
        self.close_database()

    def connect_to_database(self, db_filepath, create=False):
        """ create a database connection to a SQLite database """
        if not os.path.exists(db_filepath):
            print("Database does not exist -> create the database")
            if not create:
                print("Creation not authorized -> aborting")
                return

        try:
            self.database = sqlite3.connect(db_filepath)
        except Error as e:
            print(e)

        # Create the table is it does not exist
        create_trip_table = """
        CREATE TABLE IF NOT EXISTS trip_data(
            timestamp INTEGER NOT NULL,
            latitude NUMERIC (5, 2) NOT NULL CHECK (latitude>= -90.0 AND latitude<= 90.0),
            longitude NUMERIC (5, 2) NOT NULL CHECK (longitude>= -180.0 AND longitude<= 180.0),
            altitude NUMERIC(7, 2) NOT NULL,
            speed NUMERIC(6, 2) NOT NULL,
            km INTEGER NOT NULL CHECK (km>= 0.0),
            current_country TEXT NOT NULL,
            current_step INTEGER NOT NULL CHECK (current_step>= 0),
            PRIMARY KEY(timestamp)
        );
        """
        self.execute_query(query=create_trip_table, mode="single", create=create)

    def close_database(self):
        """ Closes the database """
        if self.database:
            self.database.close()

    def execute_query(self, query, mode, create=False, data=None):
        """
        Execute SQL query
        :param query: SQL query
        :param create: if set to True, force the creation of the table
        :param data: that comes with the query
        :return: success False if the database is not initiated or an error occurred
        """
        success = False
        if self.database or create:
            cursor = self.database.cursor()
            try:
                if mode == "multiple":
                    if data is not None:
                        cursor.executemany(query, data)
                    else:
                        cursor.execute(query)
                    self.database.commit()
                else:
                    if data is not None:
                        cursor.execute(query, data)
                    else:
                        cursor.execute(query)
                    self.database.commit()
                success = True
            except Error as e:
                print(f"The error '{e}' occurred")
        return success

    def execute_read_query(self, query):
        """
        Read the database with a SQL query
        :param query: SQL query
        :return: success, result : False if the database is not initiated or an error occurred
        """
        success = False
        result = None
        if self.database:
            cursor = self.database.cursor()
            try:
                cursor.execute(query)
                result = cursor.fetchall()
                success = True
                print(f"Query '{query}' executed successfully and resulted '{result}'")
            except Error as e:
                print(f"The error '{e}' occurred")
        return success, result

    def commit_dataframe(self, df: pd.DataFrame):
        """
        Commit position
        :param timestamp:
        :param latitude: gps latitude
        :param longitude: gps longitude
        :param altitude: elevation in meters
        :param speed: speed of the vehicle
        :param km: kilometer traveled
        :param current_step: current step
        :return:
        """
        self.query_raw_database()

        """compute km"""
        # If the kilometer source is with the GPS delta positions
        # TODO adapt to multiple rows
        #if self.kilometer_source == "GPS" and not self.raw_data.empty:
        #    if km != 0:
        #        print("The parameter kilometer_source is GPS thus the variable km=", km, " is not considered")
        #    km = round(self.raw_data["km"].iloc[-1] +
        #               distance(self.raw_data[["latitude", "lon"]].iloc[-1].values, [latitude, lon]), 2)

        """which country is the vehicle"""
        countries = []
        rg = reverse_geocoder.RGeocoder(stream=io.StringIO(open('/home/rudloff/sources/CapsuleScripts/servers/trip-overview/data/reverse_geocoder.csv', encoding='utf-8').read()))
        country_codes = pd.read_csv('/home/rudloff/sources/CapsuleScripts/servers/trip-overview/data/country_info.csv', index_col=0, error_bad_lines=False)
        # Execute on gps coords every 6 hours TODO can be optimized
        tmp_series = df["timestamp"].resample('6H').first().dropna() 
        for timestamp in tmp_series:
            tmp_latitude = df["latitude"].loc[df["timestamp"] == timestamp].values[0]
            tmp_longitude = df["longitude"].loc[df["timestamp"] == timestamp].values[0]
            countries.append(country_codes.loc[rg.query([(tmp_latitude, tmp_longitude)])[0]["cc"]]["Country"])
        tmp_df = tmp_series.to_frame()
        tmp_df["current_country"] = countries
        tmp_df.drop(["timestamp"], axis=1, inplace=True)
        df.set_index("timestamp")
        df = pd.concat([df, tmp_df], axis=1)
        df.fillna(method="bfill", inplace=True)
        df.fillna(method="ffill", inplace=True)

        insert_stmt = (
            "INSERT INTO trip_data (timestamp, latitude, longitude, altitude, speed, km, current_country, current_step) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
        )

        # Reorder the dataframe just in case
        df = df[["timestamp", "latitude", "longitude", "altitude", "speed", "km", "current_country", "current_step"]]

        if not self.execute_query(query=insert_stmt, mode="multiple", data=df.values):
            print("failed to be committed")

    def commit_position(self, timestamp, latitude, longitude, altitude, speed=-1, km=0, current_step=0):
        """
        Commit position
        :param timestamp:
        :param latitude: gps latitude
        :param longitude: gps longitude
        :param altitude: elevation in meters
        :param speed: speed of the vehicle
        :param km: kilometer traveled
        :param current_step: current step
        :return:
        """
        self.query_raw_database()

        """compute km"""
        # If the kilometer source is with the GPS delta positions
        if self.kilometer_source == "GPS" and not self.raw_data.empty:
            if km != 0:
                print("The parameter kilometer_source is GPS thus the variable km=", km, " is not considered")
            km = round(self.raw_data["km"].iloc[-1] +
                       distance(self.raw_data[["latitude", "longitude"]].iloc[-1].values, [latitude, longitude]), 2)

        """which country is the vehicle"""
        rg = reverse_geocoder.RGeocoder(stream=io.StringIO(open('data/reverse_geocoder.csv', encoding='utf-8').read()))
        country_codes = pd.read_csv('data/country_info.csv', index_col=0, error_bad_lines=False)
        current_country = country_codes.loc[rg.query([(latitude, longitude)])[0]["cc"]]["Country"]

        insert_stmt = (
            "INSERT INTO trip_data (timestamp, latitude, longitude, altitude, speed, km, current_country, current_step) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
        )
        if not self.execute_query(query=insert_stmt, mode="single",
                              data=(timestamp, latitude, longitude, altitude, speed, km, current_country, current_step)):
            print(f"Values '{timestamp, latitude, longitude, altitude, speed, km, current_country, current_step}' failed to be committed")

    def describe_trip(self):
        """
        Describe the current trip:
            - The total duration (number of days)
            - The number of country traveled
            - The total km traveled
        :return: a list of the description and a string to concatenate the values.
            for instance: (10, 2, 1405.14, "The current trip lasted 10 days, 2 country traveled to for a total of 1405.14 km")
        """
        total_duration = country_traveled = total_km_traveled = 0
        self.query_raw_database()

        """Compute the total duration"""
        data_copy = self.raw_data.copy()
        data_copy['date'] = data_copy["timestamp"].apply(
            lambda x: pd.to_datetime(x, unit="s").date())
        total_duration = (data_copy['date'].iloc[-1] - data_copy['date'].iloc[0]).days

        """Compute the total km traveled"""
        total_km_traveled = data_copy["km"].iloc[-1]

        """Compute the number of country traveled"""
        for i in range(1, len(data_copy[["latitude", "longitude"]])):
            country_traveled = len(data_copy.drop_duplicates(subset=["current_country"])["current_country"])

        return (total_duration, country_traveled, total_km_traveled,
                f"The current trip lasted {total_duration} days,"
                f" {country_traveled} country traveled for a total of {total_km_traveled} km")

    def get_last_step(self):
        """
        :return: The last step. It will return 0 if the trip has not began
        """
        # Retrieve raw position
        self.query_raw_database()
        # Copy current step raw data
        # TODO avoid copying the entire dataframe
        steps = self.raw_data.copy()

        last_step = 0
        if len(steps) > 0:
            # Get the last step
            last_step = steps["current_step"].iloc[-1]
        return last_step

    def query_raw_database(self):
        """
        Query the raw database and store it into a Pandas Dataframe
        :return: nothing but the object now store the raw_data
        """
        if self.database:
            self.raw_data = pd.read_sql_query('''SELECT * from trip_data''', self.database)

    def get_road_trip_gps_trace(self, speed_resampling=5, max_time_sampling=60):
        """
        Get the GPS trace with the sub indexed by step
        :param speed_resampling: resample the data to filter out trace where the vehicle does not move
        :param max_time_sampling: sample the data to get at most x seconds (60s by default) between traces
        :return: the road trip gps trace, ex: use dataframe.loc[10] to get the gps trace from the 9th trip step
        or use sampled[["latitude", "longitude"]] to get the whole trip gps trace
        """
        # Retrieve raw position
        self.query_raw_database()
        # Copy current step raw data
        # TODO avoid copying the entire dataframe
        gps_trace = self.raw_data.copy()
        # Change timestamp to datetime
        gps_trace['date'] = pd.to_datetime(gps_trace['timestamp'], unit='s')
        # Resample by time and interpolat linearly TODO technical debt resample by time
        # gps_trace.resample(str(max_time_sampling)+"S", on="timestamp").mean()
        # Remove the current index (the default one)
        # Remove trace static traces
        #gps_trace.drop(gps_trace[gps_trace.speed < 10.0].index, inplace=True) # TODO This is not needed anymore
        gps_trace.reset_index(drop=True, inplace=True)
        # Interpolate the correct columns
        gps_trace[["latitude", "longitude", "altitude", "speed", "km"]] = gps_trace[["latitude", "longitude", "altitude", "speed", "km"]].interpolate(
            method='linear')
        # Fill forward current_country and current_step
        gps_trace["current_country"].fillna(method='ffill', inplace=True)
        gps_trace["current_step"].fillna(method='ffill', inplace=True)
        # Reset the current_step type
        gps_trace["current_step"] = gps_trace["current_step"].astype('int64')
        # Set current_step as index
        gps_trace = gps_trace.set_index(['current_step'])
        return gps_trace

    def wrap_to_geojson(x):
        line = geojson.LineString((x["latitude"], x["longitude"]))
        properties = {'times': x["timestamp"],
                      'icon': 'circle',
                      'iconstyle':
                          {'fillColor': '#d6604d',
                           'fillOpacity': 0.8,
                           'stroke': 'true',
                           'radius': 7}}
        return [geojson.Feature(geometry=line, properties=properties)]

    def get_sleeping_locations(self, static_position_threshold=1, min_distance=10):
        """
        With the given gps positions filter the positions where the vehicle slept.
        :param static_position_threshold: maximal speed of the position to consider the position as sleeping position
            unit: second
            min: > 0, max: inf
            default: 1
        :param min_distance: minimal distance between sleeping positions to consider
            unit km
            min > 0, max: inf
            default: 10
        :return: pandas.DataFrame sleeping positions [timestamp, latitude, longitude, altitude]
        """
        # Parameter safeguards
        if static_position_threshold <= 0:
            print("The parameter static_position_threshold value is not within (0 and inf)")
            return None
        if min_distance <= 0:
            print("The parameter min_distance value is not within (0 and inf)")
            return None

        # Retrieve raw position
        self.query_raw_database()
        sleeping_df = self.raw_data.copy()
        # Filter the static position
        sleeping_df = sleeping_df[sleeping_df.speed <= static_position_threshold]
        # Get the dates
        sleeping_df['date'] = sleeping_df["timestamp"].apply(lambda x: pd.to_datetime(x, unit="s").date())
        # Filter the last position of the day
        sleeping_df = sleeping_df.drop_duplicates(subset=["date"], keep='last')

        # Compute distance to each other
        sleeping_df["dist_from_last"] = 0.0
        for i in range(1, len(sleeping_df[["latitude", "longitude"]])):
            sleeping_df["dist_from_last"].iloc[i] = distance(sleeping_df[["latitude", "longitude"]].iloc[i - 1].values,
                                                             sleeping_df[["latitude", "longitude"]].iloc[i].values)
        # Filter positions that distance is sufficient
        sleeping_df = sleeping_df[sleeping_df.dist_from_last >= min_distance]
        return sleeping_df[["timestamp", "latitude", "longitude", "altitude"]].copy()
