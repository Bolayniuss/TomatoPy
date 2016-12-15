# -*- coding: utf8 -*-
from __future__ import print_function, absolute_import, unicode_literals

import unittest

from TomatoPy.scrappers.scrappers import BetaserieRSSScrapper


class BetaSeriesTestCase(unittest.TestCase):
    def setUp(self):
        self.scrapper = BetaserieRSSScrapper("bolaynius_test")
        self.episodes = self.scrapper.get_episodes()

    def test_betaseries(self):
        self.assertEqual(self.episodes[0].title, "Crossed S01E01")
        self.assertEqual(self.episodes[0].tv_show, "Crossed")
        self.assertEqual(self.episodes[0].season, "1")
        self.assertEqual(self.episodes[0].episode_number, "1")


if __name__ == '__main__':
    unittest.main()
