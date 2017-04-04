# -*- coding: utf8 -*-
from __future__ import print_function, absolute_import, unicode_literals

import unittest

from TomatoPy.scrappers.scrappers import BetaserieRSSScrapper, T411Scrapper


class BetaSeriesTestCase(unittest.TestCase):
    def setUp(self):
        self.scrapper = BetaserieRSSScrapper("bolaynius_test")
        self.episodes = self.scrapper.get_episodes()

    def test_scrapper_ok(self):
        self.assertEqual(self.episodes[0].title, "Crossed S01E01")
        self.assertEqual(self.episodes[0].tv_show, "Crossed")
        self.assertEqual(self.episodes[0].season, 1)
        self.assertEqual(self.episodes[0].episode_number, 1)


class T411TestCase(unittest.TestCase):
    def setUp(self):
        self.scrapper = T411Scrapper("bolay", "12081987")
        self.episodes = self.scrapper.get_torrents("Homeland")

    def test_scrapper_result_ok(self):
        self.assertGreater(len(self.episodes), 0)
        e = self.episodes[0]
        self.assertIn("Homeland", e.title)
        self.assertTrue(callable(e._content))
        self.assertIsNotNone(e.content)


if __name__ == '__main__':
    unittest.main()
