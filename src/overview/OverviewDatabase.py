import sqlite3
from sqlite3 import Error
import pandas as pd
import geojson
import os
import io
import math
import reverse_geocoder


def distance(origin, destination):
    """TODO doc
    Haversine formula example in Python
    Author: Wayne Dyck
    https://gist.github.com/rochacbruno/2883505
    """
    lat1, lon1 = origin
    lat2, lon2 = destination
    radius = 6371  # earth radius in km

    diff_lat = math.radians(lat2-lat1)
    diff_lon = math.radians(lon2-lon1)
    a = math.sin(diff_lat/2) * math.sin(diff_lat/2) + math.cos(math.radians(lat1)) \
        * math.cos(math.radians(lat2)) * math.sin(diff_lon/2) * math.sin(diff_lon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    d = radius * c

    return d


class OverviewDatabase:
    """This class wraps the Folium TimestampGeoJson class to add functions like
    connecting to a database with simple custom geographic position"""
    # timestamp_geo_json = TimestampGeoJsonWrapper("file")
    # timestamp_geo_json.query_positions()

    # Database instance
    database = None
    raw_data = None
    geojsondata = None
    kilometer_source = "GPS" # Could be GPS (default) or ODO

    def __init__(self, kilometer_source="GPS"):
        """ Initiation """
        self.raw_data = None
        self.geojsondata = None
        self.kilometer_source = kilometer_source

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
            lat NUMERIC (5, 2) NOT NULL CHECK (lat>= -90.0 AND lat<= 90.0),
            lon NUMERIC (5, 2) NOT NULL CHECK (lon>= -180.0 AND lon<= 180.0),
            elev NUMERIC(7, 2) NOT NULL,
            speed NUMERIC(6, 2) NOT NULL,
            km INTEGER NOT NULL CHECK (km>= 0.0),
            current_country TEXT NOT NULL,
            current_step INTEGER NOT NULL CHECK (current_step>= 0),
            PRIMARY KEY(timestamp)
        );
        """
        self.execute_query(query=create_trip_table, create=create)

    def close_database(self):
        """ Closes the database """
        if self.database:
            self.database.close()

    def execute_query(self, query, create=False, data=None):
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
                if data is not None:
                    cursor.execute(query, data)
                else:
                    cursor.execute(query)
                self.database.commit()
                success = True
                print(f"Query '{query}' executed successfully to enter those data:", data)
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

    def commit_position(self, timestamp, lat, lon, elev, speed=-1, km=0, current_step=-1):
        """
        Commit position
        :param timestamp:
        :param lat: gps latitude
        :param lon: gps longitude
        :param elev: elevation in meters
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
                       distance(self.raw_data[["lat", "lon"]].iloc[-1].values, [lat, lon]), 2)

        """which country is the vehicle"""
        rg = reverse_geocoder.RGeocoder(stream=io.StringIO(open('data/reverse_geocoder.csv', encoding='utf-8').read()))
        country_codes = pd.read_csv('data/country_info.csv', index_col=0, error_bad_lines=False)
        current_country = country_codes.loc[rg.query([(lat, lon)])[0]["cc"]]["Country"]

        insert_stmt = (
            "INSERT INTO trip_data (timestamp, lat, lon, elev, speed, km, current_country, current_step) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
        )
        if not self.execute_query(query=insert_stmt,
                              data=(timestamp, lat, lon, elev, speed, km, current_country, current_step)):
            print(f"Values '{timestamp, lat, lon, elev, speed, km, current_country, current_step}' failed to be committed")

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
        for i in range(1, len(data_copy[["lat", "lon"]])):
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

    def wrap_to_geojson(x):
        line = geojson.LineString((x["lat"], x["lon"]))
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
        :return: pandas.DataFrame sleeping positions [timestamp, lat, lon, elev]
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
        for i in range(1, len(sleeping_df[["lat", "lon"]])):
            sleeping_df["dist_from_last"].iloc[i] = distance(sleeping_df[["lat", "lon"]].iloc[i - 1].values,
                                                             sleeping_df[["lat", "lon"]].iloc[i].values)
        # Filter positions that distance is sufficient
        sleeping_df = sleeping_df[sleeping_df.dist_from_last >= min_distance]
        return sleeping_df[["timestamp", "lat", "lon", "elev"]].copy()


#timestamp_geo_json = OverviewDatabase()
#timestamp_geo_json.connect_to_database("file")
#timestamp_geo_json.commit_position(1041234, 45.0, 35.5, 1004.0, 10.0)
#timestamp_geo_json.query_raw_positions()
