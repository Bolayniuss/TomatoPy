# -*- coding: utf-8 -*-
# 


import os
import sys

sys.path.insert(1, os.path.join(sys.path[0], '..'))

from TomatoPy.scrappers.scrappers import ShowRSSScrapper

a = ShowRSSScrapper("209022")

episodes = a.get_episodes()
for episode in episodes:
	print episode.torrentProvided
	print episode


