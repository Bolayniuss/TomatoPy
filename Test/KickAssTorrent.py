# -*- coding: utf-8 -*-
# 


import os
import sys

sys.path.insert(1, os.path.join(sys.path[0], '..'))

from TomatoPy.scrappers.scrappers import KickAssTorrentScrapper

kat = KickAssTorrentScrapper()

torrents = kat.get_torrents("the big bang theory s08e11")
for torrent in torrents:
    print torrent


