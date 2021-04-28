import os
import unittest
import numpy as np
from unittest import TestCase
from src.overview.OverviewDatabase import OverviewDatabase


class TestOverviewDatabase(TestCase):
    unit_test_data_folder = os.path.join(os.getcwd(), "tests", "unit", "data")

    def test_connect_to_database_not_exist(self):
        # Database does not exist
        timestamp_geo_json = OverviewDatabase()
        timestamp_geo_json.connect_to_database(os.path.join(self.unit_test_data_folder, "no_database.db"))
        self.assertEqual(timestamp_geo_json.database is None, True)
        timestamp_geo_json.close_database()

        # Database does not exist
        timestamp_geo_json = OverviewDatabase()
        timestamp_geo_json.connect_to_database(os.path.join(self.unit_test_data_folder, "no_database.db"), False)
        self.assertEqual(timestamp_geo_json.database is None, True)
        timestamp_geo_json.close_database()

        # Database does not exist let it create
        timestamp_geo_json = OverviewDatabase()
        timestamp_geo_json.connect_to_database(os.path.join(self.unit_test_data_folder, "create_database.db"), True)
        self.assertEqual(timestamp_geo_json.database is None, False)
        timestamp_geo_json.close_database()

        # Remove test.db generated if exists
        if os.path.exists(os.path.join(self.unit_test_data_folder, "create_database.db")):
            os.remove(os.path.join(self.unit_test_data_folder, "create_database.db"))

    def test_connect_to_database_exist(self):
        timestamp_geo_json = OverviewDatabase()
        timestamp_geo_json.connect_to_database(os.path.join(self.unit_test_data_folder, "database_exists.db"), True)
        self.assertEqual(timestamp_geo_json.database is None, False)
        timestamp_geo_json.close_database()

        timestamp_geo_json = OverviewDatabase()
        timestamp_geo_json.connect_to_database(os.path.join(self.unit_test_data_folder, "database_exists.db"))
        self.assertEqual(timestamp_geo_json.database is None, False)
        timestamp_geo_json.close_database()

        timestamp_geo_json = OverviewDatabase()
        timestamp_geo_json.connect_to_database(os.path.join(self.unit_test_data_folder, "database_exists.db"), False)
        self.assertEqual(timestamp_geo_json.database is None, False)
        timestamp_geo_json.close_database()

    def test_sleeping_position_safeguard(self):
        # Test safeguards
        timestamp_geo_json = OverviewDatabase()
        timestamp_geo_json.connect_to_database(os.path.join(self.unit_test_data_folder, "sleeping_positions.db"))
        sleeping_position = timestamp_geo_json.get_sleeping_locations(static_position_threshold=-1.0,
                                                                      min_distance=10000.0)
        self.assertEqual(sleeping_position, None)

        sleeping_position = timestamp_geo_json.get_sleeping_locations(static_position_threshold=-1.0,
                                                                      min_distance=-10000.0)
        self.assertEqual(sleeping_position, None)

        sleeping_position = timestamp_geo_json.get_sleeping_locations(static_position_threshold=1.0,
                                                                      min_distance=-10000.0)
        self.assertEqual(sleeping_position, None)
        timestamp_geo_json.close_database()

    def test_sleeping_position_algo(self):
        # Test the algorithm (arr_to_compare was previously computed and retrieve from known database)
        timestamp_geo_json = OverviewDatabase()
        timestamp_geo_json.connect_to_database(os.path.join(self.unit_test_data_folder, "sleeping_positions.db"))
        sleeping_position = timestamp_geo_json.get_sleeping_locations(static_position_threshold=1.0,
                                                                      min_distance=10000.0)
        arr_to_compare = [[1619634065.0, 49.431277595698134, -20.98148729661071, 1514.1521730711734],
                             [1621194065.0, -86.1098956684625, 35.234345656375524, 80.3408834444651],
                             [1621834065.0, -42.826527934121025, -79.58012428574254, 1618.3108108719073],
                             [1621994065.0, -7.954232329795332, 35.788277401957856, 1883.3508097831768],
                             [1625414065.0, -84.90846986361606, 127.82413463655297, 1961.8996930060061],
                             [1627274065.0, 54.224022710287215, 41.515787809682706, 1578.9008688644137],
                             [1627354065.0, -75.42843316666324, 170.47262816944078, 1940.6388351476155],
                             [1629694065.0, 38.53138915290043, -156.4687100166362, 598.0491877891006],
                             [1630174065.0, -82.73484030998364, 142.85054919092374, 637.8919991016945],
                             [1630954065.0, 72.87019994033659, 162.48060405168206, 602.1519613980629],
                             [1632654065.0, -60.83675755429996, 10.412778726866492, 439.6424213817743],
                             [1633014065.0, -44.367148322343496, 172.85962955561644, 1974.9541260630958],
                             [1633434065.0, 53.71556212499095, 156.31537796737825, 496.5989531307573],
                             [1633614065.0, -54.71120904181415, 18.816344922429494, 1559.9148077377374],
                             [1634294065.0, 55.29434787181489, -65.96615858183169, 798.7524857699054],
                             [1638554065.0, -76.65452037125489, -30.04423329175023, 970.5383400465591]]
        self.assertEqual(sleeping_position.values.tolist(), arr_to_compare)
        timestamp_geo_json.close_database()

    def test_last_step(self):
        timestamp_geo_json = OverviewDatabase()
        timestamp_geo_json.connect_to_database(os.path.join(self.unit_test_data_folder, "no_last_step.db"))
        last_step = timestamp_geo_json.get_last_step()
        timestamp_geo_json.close_database()
        self.assertEqual(last_step, 0)

        timestamp_geo_json = OverviewDatabase()
        timestamp_geo_json.connect_to_database(os.path.join(self.unit_test_data_folder, "with_last_step.db"))
        last_step = timestamp_geo_json.get_last_step()
        timestamp_geo_json.close_database()
        self.assertEqual(last_step, 2)

    def test_describe_trip(self):
        timestamp_geo_json = OverviewDatabase()
        timestamp_geo_json.connect_to_database(os.path.join(self.unit_test_data_folder, "describe.db"))
        describe = timestamp_geo_json.describe_trip()
        timestamp_geo_json.close_database()
        self.assertEqual(describe, (11, 1, 10,
                                    "The current trip lasted 11 days, 1 country traveled for a total of 10 km"))

    def test_commit(self):
        timestamp_geo_json = OverviewDatabase()
        timestamp_geo_json.connect_to_database(os.path.join(self.unit_test_data_folder, "create_describe.db"), True)
        timestamp_geo_json.commit_position(1, 49.0659719561271, 1.99154344325376, 10, 30, 10, 0)
        timestamp_geo_json.commit_position(1000000, 49.0694584269596, 2.0623537554957, 10, 30, 11, 1)
        describe = timestamp_geo_json.describe_trip()
        timestamp_geo_json.close_database()
        self.assertEqual(describe, (11, 1, 15.17,
                                    "The current trip lasted 11 days, 1 country traveled for a total of 15.17 km"))

        # Remove test.db generated if exists
        if os.path.exists(os.path.join(self.unit_test_data_folder, "create_describe.db")):
            os.remove(os.path.join(self.unit_test_data_folder, "create_describe.db"))

    def test_gps_trace(self):
        timestamp_geo_json = OverviewDatabase()
        timestamp_geo_json.connect_to_database(os.path.join(self.unit_test_data_folder, "gps_trace.db"), True)
        trace = timestamp_geo_json.get_road_trip_gps_trace(speed_resampling=10)
        timestamp_geo_json.close_database()
        self.assertEqual(trace.loc[0]["lat"].values[0] == 46.58568968857452, True)
        self.assertEqual(trace.loc[0]["lat"].values[1] == -53.46602430039604, True)
        self.assertEqual(trace.loc[3]["lat"].values[0] == 59.45381512533035, True)
        self.assertEqual(trace["lat"].values[4] == 59.45381512533035, True)


if __name__ == '__main__':
    unittest.main()
