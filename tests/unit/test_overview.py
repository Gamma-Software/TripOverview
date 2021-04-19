import os
import unittest
from unittest import TestCase
from src.overview.OverviewDatabase import OverviewDatabase


class TestOverviewDatabase(TestCase):
    unit_test_data_folder = os.path.join(os.getcwd(), "tests", "unit", "data")

    def test_connect_to_database_not_exist(self):
        # Database does not exist
        timestamp_geo_json = OverviewDatabase()
        timestamp_geo_json.connect_to_database(os.path.join(self.unit_test_data_folder, "test.db"))
        self.assertEqual(timestamp_geo_json.database is None, True)
        timestamp_geo_json.close_database()

        # Database does not exist
        timestamp_geo_json = OverviewDatabase()
        timestamp_geo_json.connect_to_database(os.path.join(self.unit_test_data_folder, "test.db"), False)
        self.assertEqual(timestamp_geo_json.database is None, True)
        timestamp_geo_json.close_database()

        # Database does not exist let it create
        timestamp_geo_json = OverviewDatabase()
        timestamp_geo_json.connect_to_database(os.path.join(self.unit_test_data_folder, "test.db"), True)
        self.assertEqual(timestamp_geo_json.database is None, False)
        timestamp_geo_json.close_database()

        # Remove test.db generated if exists
        if os.path.exists(os.path.join(self.unit_test_data_folder, "test.db")):
            os.remove(os.path.join(self.unit_test_data_folder, "test.db"))

    def test_connect_to_database_exist(self):
        timestamp_geo_json = OverviewDatabase()
        print(os.getcwd())
        timestamp_geo_json.connect_to_database(os.path.join(self.unit_test_data_folder, "pythonsqlite.db"), True)
        self.assertEqual(timestamp_geo_json.database is None, False)
        timestamp_geo_json.close_database()

        timestamp_geo_json = OverviewDatabase()
        timestamp_geo_json.connect_to_database(os.path.join(self.unit_test_data_folder, "pythonsqlite.db"))
        self.assertEqual(timestamp_geo_json.database is None, False)
        timestamp_geo_json.close_database()

        timestamp_geo_json = OverviewDatabase()
        timestamp_geo_json.connect_to_database(os.path.join(self.unit_test_data_folder, "pythonsqlite.db"), False)
        self.assertEqual(timestamp_geo_json.database is None, False)
        timestamp_geo_json.close_database()

    def test_sleeping_position_safeguard(self):
        # Test safeguards
        timestamp_geo_json = OverviewDatabase()
        timestamp_geo_json.connect_to_database(os.path.join(self.unit_test_data_folder, "pythonsqlite.db"))
        sleeping_position = timestamp_geo_json.get_sleeping_locations(static_position_threshold=-1.0,
                                                                      min_distance=10000.0)
        self.assertEqual(sleeping_position, None)

        sleeping_position = timestamp_geo_json.get_sleeping_locations(static_position_threshold=-1.0,
                                                                      min_distance=-10000.0)
        self.assertEqual(sleeping_position, None)

        sleeping_position = timestamp_geo_json.get_sleeping_locations(static_position_threshold=1.0,
                                                                      min_distance=-10000.0)
        self.assertEqual(sleeping_position, None)

    def test_sleeping_position_algo(self):
        # Test the algorithm (arr_to_compare was previously computed and retrieve from known database)
        timestamp_geo_json = OverviewDatabase()
        timestamp_geo_json.connect_to_database(os.path.join(self.unit_test_data_folder, "pythonsqlite.db"))
        sleeping_position = timestamp_geo_json.get_sleeping_locations(static_position_threshold=1.0,
                                                                      min_distance=10000.0)
        arr_to_compare = [[1618820065.0, -49.78690939348198, -3.805875048742564, -84.47370043631621],
                          [1618936065.0, 37.13415931996609, 179.00562167415478, 412.7214569389232],
                          [1618994065.0, -9.83469485563809, -35.75825919803481, 688.4604363848367],
                          [1619200065.0, 49.10854041902809, -144.70545444081387, -40.65572220233265],
                          [1619258065.0, -59.176027937074196, 112.0352349203165, 570.6795476207768],
                          [1619544065.0, -75.03506256640486, 57.78561399733644, 860.1709928073229],
                          [1619734065.0, 73.85356360901267, 113.16560472344452, 787.4086088312232],
                          [1619746065.0, -30.011845773073645, -150.48487842130208, 1549.7752073372694],
                          [1620140065.0, 28.19190068663478, 117.92338615287599, 1428.013416142928],
                          [1620256065.0, -43.17996948492938, -28.40686355209135, 999.2290435846639],
                          [1620394065.0, 39.67410695295811, 30.809351967524776, 862.7258185399526],
                          [1620512065.0, -68.90706422529061, -70.42216768231695, 1674.466900226373],
                          [1620742065.0, 78.29148861767439, -108.94832646361277, 599.0045583237422],
                          [1620850065.0, -79.52130256523658, 156.81823342705684, 1450.9797053383274],
                          [1621032065.0, 19.921294159216274, 162.47794400338074, 1686.3926625304277],
                          [1621206065.0, -65.61426592379706, 152.7874024853577, 1660.814508914641],
                          [1621272065.0, 65.56650534378679, -152.20970971831383, 136.54790141266858],
                          [1621340065.0, -41.466615989799635, 56.24459724742093, 694.8145263082174],
                          [1621894065.0, 10.723964812681018, -131.71535211282134, 1248.2564223310246],
                          [1622038065.0, -53.79019529092054, 97.42498161064202, 380.9929525750793],
                          [1622142065.0, 60.268767375171564, 176.48082179931674, 323.0296889952723],
                          [1622192065.0, -82.35238665518891, -55.17291712220019, 1915.6455951554658],
                          [1622294065.0, 32.17682481821515, -124.3467174563323, 67.93160418836774],
                          [1622432065.0, -14.91340773935437, 42.82529433417446, 223.81945003652766],
                          [1622746065.0, -27.949979158501407, -142.8203118402694, 863.0530667251164]]
        self.assertEqual(sleeping_position.values.tolist(), arr_to_compare)

    def test_last_step(self):
        timestamp_geo_json = OverviewDatabase()
        timestamp_geo_json.connect_to_database(os.path.join(self.unit_test_data_folder, "no_last_step.db"))
        last_step = timestamp_geo_json.get_last_step()
        self.assertEqual(last_step, 0)

        timestamp_geo_json = OverviewDatabase()
        timestamp_geo_json.connect_to_database(os.path.join(self.unit_test_data_folder, "last_step.db"))
        last_step = timestamp_geo_json.get_last_step()
        self.assertEqual(last_step, 1)


if __name__ == '__main__':
    unittest.main()
