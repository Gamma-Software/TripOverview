import sqlite3
from sqlite3 import Error
import pandas as pd
import geojson
import os
import math


def distance(origin, destination):
    """TODO doc
    Haversine formula example in Python
    Author: Wayne Dyck
    https://gist.github.com/rochacbruno/2883505
    """
    lat1, lon1 = origin
    lat2, lon2 = destination
    radius = 6371 # km

    dlat = math.radians(lat2-lat1)
    dlon = math.radians(lon2-lon1)
    a = math.sin(dlat/2) * math.sin(dlat/2) + math.cos(math.radians(lat1)) \
        * math.cos(math.radians(lat2)) * math.sin(dlon/2) * math.sin(dlon/2)
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

    def __init__(self):
        self.raw_data = None
        self.geojsondata = None

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
        create_users_table = """
        CREATE TABLE IF NOT EXISTS trip_geo (
          timestamp INTEGER TIMESTAMP,
          lat FLOAT LATITUDE,
          lon FLOAT LONGITUDE,
          elev FLOAT ELEVATION,
          speed FLOAT SPEED,
          current_step INT CURRENT_STEP
        );
        """
        self.execute_query(query=create_users_table, create=create)

    def close_database(self):
        if self.database:
            self.database.close()

    def execute_query(self, query, create=False, data=None):
        if self.database or create:
            cursor = self.database.cursor()
            try:
                if data is not None:
                    cursor.execute(query, data)
                else:
                    cursor.execute(query)
                self.database.commit()
                print("Query executed successfully")
            except Error as e:
                print(f"The error '{e}' occurred")

    def execute_read_query(self, query):
        if self.database:
            cursor = self.database.cursor()
            result = None
            try:
                cursor.execute(query)
                result = cursor.fetchall()
                return result
            except Error as e:
                print(f"The error '{e}' occurred")

    def commit_position(self, timestamp, lat, lon, elev, speed, current_step=-1):
        insert_stmt = (
            "INSERT INTO trip_geo (timestamp, lat, lon, elev, speed, current_step) "
            "VALUES (?, ?, ?, ?, ?, ?)"
        )
        self.execute_query(query=insert_stmt, data=(timestamp, lat, lon, elev, speed, current_step))

    def get_last_step(self):
        """
        :return: The last step. It will return 0 if the trip has not began
        """
        # Retrieve raw position
        self.query_raw_positions()
        # Copy current step raw data
        steps = self.raw_data["current_step"]
        # Filter out the -1 steps
        steps = steps[steps.current_step != -1]

        last_step = 0
        if len(steps) > 0:
            # Get the last step
            last_step = steps["current_step"].iloc[-1]
        return last_step

    def query_raw_positions(self, force=False):
        if self.database:
            if force or not self.raw_data:
                self.raw_data = pd.read_sql_query('''SELECT * from trip_geo''', self.database)

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
        self.query_raw_positions()
        sleeping_df = self.raw_data
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
        return sleeping_df[["timestamp", "lat", "lon", "elev"]]


#timestamp_geo_json = OverviewDatabase()
#timestamp_geo_json.connect_to_database("file")
#timestamp_geo_json.commit_position(1041234, 45.0, 35.5, 1004.0, 10.0)
#timestamp_geo_json.query_raw_positions()
