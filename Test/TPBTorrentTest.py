# -*- coding: utf-8 -*-
# TomatoPy
from __future__ import absolute_import, unicode_literals, print_function

import logging
logging.basicConfig(level=logging.DEBUG)

from TomatoPy.scrappers.scrappers import TPBScrapper
from multi_host import MultiHostHandler

MultiHostHandler.Instance().register_multi_host("thepiratebay.org", [
        "thepiratebay.se",
        "thepiratebay.cr",
        "pirateproxy.bz",
        "labaia.in",
        "bay.dragonflame.org",
        "thepiratebay.mine.nu",
        "rghmodding.com",
        "torrentula.se",
        "baytorrent.eu"
])

tpb = TPBScrapper()

torrents = tpb.get_torrents("Family Guy S15E07")
for torrent in torrents:
    print(torrent)