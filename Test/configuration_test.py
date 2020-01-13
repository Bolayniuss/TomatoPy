# -*- coding: utf-8 -*-
# 


import unittest

import configuration


class BasicConfig(configuration.Configurable):
    defaultSettings = {"p0": 1, "p1": "bla", "p2": 0.1}

    def __init__(self, p0, p1, p2):
        self.p0 = p0
        self.p1 = p1
        self.p2 = p2

    def get_settings(self):
        return {"p0": self.p0, "p1": self.p1, "p2": self.p2}


class ConfigurationTest(unittest.TestCase):
    def setUp(self):
        self.path = "settings.test.json"
        self.config = configuration.Configuration(self.path)

    def test_settings_generate(self):
        element = configuration.createConfigurable(BasicConfig, self.config)
        self.assertEqual(element.get_settings(), element.defaultSettings, "Settings load/save test failed.")

    def test_settings_save_load(self):
        self.config = configuration.Configuration(self.path)
        self.config.load()
        element = configuration.createConfigurable(BasicConfig, self.config)
        v = "New"
        element.p2 = v
        self.config.save()
        self.config = configuration.Configuration(self.path)
        self.config.load()
        element = configuration.createConfigurable(BasicConfig, self.config)
        self.assertEqual(element.p2, v)


if __name__ == '__main__':
    unittest.main()
