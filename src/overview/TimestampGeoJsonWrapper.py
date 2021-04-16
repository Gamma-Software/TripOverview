import sqlite3
from sqlite3 import Error
import pandas as pd
import geojson


class TimestampGeoJsonWrapper:
    """This class wraps the Folium TimestampGeoJson class to add functions like
    connecting to a database with simple custom geographic position"""
    # timestamp_geo_json = TimestampGeoJsonWrapper("file")
    # timestamp_geo_json.query_positions()

    # Database instance
    database = None
    geojsondata = None

    def __init__(self, db_filepath):
        self.connection = self.create_connection(db_filepath)
        self.geojsondata = None

    def create_connection(self, db_file):
        """ create a database connection to a SQLite database """
        try:
            self.database = sqlite3.connect(db_file)
            print(sqlite3.version)
        except Error as e:
            print(e)

        # Create the table is it does not exist
        create_users_table = """
        CREATE TABLE IF NOT EXISTS trip_geo (
          timestamp INTEGER TIMESTAMP,
          lat FLOAT LATITUDE,
          lon FLOAT LONGITUDE,
          elev FLOAT ELEVATION
        );
        """
        self.execute_query(self.connection, create_users_table)
        return self.connection

    def execute_query(self, query, data=None):
        cursor = self.connection.cursor()
        try:
            if data is not None:
                cursor.execute(query, data)
            else:
                cursor.execute(query)
            self.connection.commit()
            print("Query executed successfully")
        except Error as e:
            print(f"The error '{e}' occurred")

    def execute_read_query(self, query):
        cursor = self.connection.cursor()
        result = None
        try:
            cursor.execute(query)
            result = cursor.fetchall()
            return result
        except Error as e:
            print(f"The error '{e}' occurred")

    def commit_position(self, timestamp, position):
        insert_stmt = (
            "INSERT INTO trip_geo (timestamp, lat, lon, elev) "
            "VALUES (?, ?, ?, ?)"
        )
        self.execute_query(insert_stmt, (timestamp, position.lat, position.lon))

    def query_positions(self):
        self.geojsondata = self.pandas2geojson(pd.read_sql_query('''SELECT * from trip_geo''', self.connection))

    def pandas2geojson(self, df):
        features = []
        insert_features = lambda x: features.append(
            geojson.Feature(geometry=geojson.LineString((x["lat"],
                                                         x["lon"],
                                                         x["elev"])),
                            properties=dict(times=x["timestamp"],
                                            style={'color': '#d6604d'},
                                            icon='circle',
                                            iconstyle={
                                                'fillColor': '#d6604d',
                                                'fillOpacity': 0.8,
                                                'stroke': 'true',
                                                'radius': 7
                                            })))
        df.apply(insert_features, axis=1)
        return geojson.FeatureCollection(features)


#timestamp_geo_json = TimestampGeoJsonWrapper("file")
#timestamp_geo_json.query_positions()
