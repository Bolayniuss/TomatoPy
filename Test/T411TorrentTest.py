# -*- coding: utf-8 -*-
# TomatoPy
from __future__ import absolute_import, unicode_literals, print_function

import logging
logging.basicConfig(level=logging.DEBUG)

from TomatoPy.scrappers.scrappers import T411Scrapper

tpb = T411Scrapper("bolay", "12081987")

torrents = tpb.get_torrents("un village")
for torrent in torrents:
    print(torrent)