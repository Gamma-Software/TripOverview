import sqlite3
from sqlite3 import Error


class TimestampGeoJsonWrapper:
    """This class wraps the Folium TimestampGeoJson class to add functions like
    connecting to a database with simple custom geographic position"""

    # Database instance
    database = None

    def __init__(self, db_file):
        self.connection = self.create_connection(db_file)

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
          lon FLOAT LONGITUDE
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

    def commit_position(self, timestamp, position):
        insert_stmt = (
            "INSERT INTO trip_geo (timestamp, lat, lon) "
            "VALUES (?, ?, ?)"
        )
        self.execute_query(insert_stmt, (timestamp, position.lat, position.lon))

#if __name__ == '__main__':
#    connection = create_connection(r"D:\sources\perso\TripOverview\prototype\data\pythonsqlite.db")