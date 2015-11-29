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
        self.assertEqual(len(self.episodes), 28, "")

    def test_list(self):
        print self.episodes[0].title
        print self.episodes[0].tvShow
        print self.episodes[0].season
        print self.episodes[0].episodeNumber


if __name__ == '__main__':
    unittest.main()
