# -*- coding: utf-8 -*-
# TomatoPy

__author__ = 'Michael Bolay'

import unittest
from TomatoPy.Scrapper import BetaserieRSSScrapper


class BetaSeriesTestCase(unittest.TestCase):
    def setUp(self):
        self.scrapper = BetaserieRSSScrapper("bolaynius_test")
        self.episodes = self.scrapper.getEpisodes()

    def test_betaseries(self):
        self.assertEqual(self.episodes[0].title, "Crossed S01E01")
        self.assertEqual(self.episodes[0].tvShow, "Crossed")
        self.assertEqual(self.episodes[0].season, "1")
        self.assertEqual(self.episodes[0].episodeNumber, "1")


if __name__ == '__main__':
    unittest.main()
