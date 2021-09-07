import unittest
from unittest import TestCase
from script.methods import dist_from_gps


class TestMethods(TestCase):
    def test_dist_from_gps(self):
        self.assertEqual(round(dist_from_gps([52.2296756, 21.0122287], [52.406374, 16.9251681]), 3), 278.546) 

        
if __name__ == '__main__':
    unittest.main()