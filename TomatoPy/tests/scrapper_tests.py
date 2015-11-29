# -*- coding: utf-8 -*-
# TomatoPy

__author__ = 'Michael Bolay'

import unittest
from TomatoPy.Scrapper import BetaserieRSSScrapper


class MyTestCase(unittest.TestCase):
    def test_betaseries(self):

        scrapper = BetaserieRSSScrapper("bolayniuss_test")
        episodes = scrapper.getEpisodes()

        self.assertEqual(len(episodes), 56, "")


if __name__ == '__main__':
    unittest.main()
