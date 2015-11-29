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
        self.assertEqual(len(self.episodes), 56, "")

    def test_list(self):
        for e in self.episodes:
            print e


if __name__ == '__main__':
    unittest.main()
